"""Document indexing worker.

Consumes index_document jobs from the queue, processes file content extraction,
computes content hashes, and updates document status.

Run with:  python -m app.workers.indexer
"""

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.database import get_db
from app.database.engine import DatabaseConnection
from app.database.repositories.document import DocumentRepository
from app.services.queue import job_queue

logger = logging.getLogger("nebula.indexer")
settings = get_settings()


class IndexingWorker:
    """Worker that processes document indexing jobs."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.base_delay = settings.indexing_retry_base_delay
        self.backoff_multiplier = settings.indexing_retry_backoff_multiplier
        self._db: DatabaseConnection | None = None

    async def connect(self) -> None:
        """Initialize database connection pool."""
        from app.database import init_db
        await init_db()
        logger.info("Indexing worker connected to database")

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def _get_db(self) -> DatabaseConnection:
        """Get or create database connection."""
        if self._db is None:
            self._db = await get_db()
        return self._db

    async def _validate_ownership(self, doc_id: int, user_id: int, db: DatabaseConnection) -> bool:
        """Validate that the document belongs to the requesting user."""
        doc = await db.fetchone(
            "SELECT id, user_id FROM documents WHERE id = ?",
            (doc_id,)
        )
        if not doc:
            logger.warning("Document %d not found", doc_id)
            return False
        if doc["user_id"] != user_id:
            logger.warning(
                "Ownership validation failed: doc %d belongs to user %d, job requested user %d",
                doc_id, doc["user_id"], user_id
            )
            return False
        return True

    async def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _extract_content(self, file_path: str) -> str:
        """Extract text content from file based on extension."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        ext = path.suffix.lower()

        # Use asyncio.to_thread to avoid blocking the event loop
        if ext == ".pdf":
            return await asyncio.to_thread(self._extract_pdf, path)
        elif ext == ".docx":
            return await asyncio.to_thread(self._extract_docx, path)
        else:
            return await asyncio.to_thread(self._extract_text, path)

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF file using pypdf."""
        try:
            import pypdf
        except ImportError:
            raise RuntimeError(
                "pypdf is required for PDF extraction. Install with: pip install pypdf"
            )

        text_parts = []
        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    def _extract_docx(self, path: Path) -> str:
        """Extract text from DOCX file using python-docx."""
        try:
            import docx
        except ImportError:
            raise RuntimeError(
                "python-docx is required for DOCX extraction. Install with: pip install python-docx"
            )

        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)

    def _extract_text(self, path: Path) -> str:
        """Extract text from plain text files (TXT, MD, CSV, JSON, HTML)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, "r", encoding="latin-1") as f:
                return f.read()

    async def _update_status(
        self,
        doc_id: int,
        status: str,
        content_hash: str | None = None,
        error_message: str | None = None,
        db: DatabaseConnection | None = None,
    ) -> None:
        """Update document status and related fields."""
        if db is None:
            db = await self._get_db()

        if content_hash:
            await db.execute(
                "UPDATE documents SET status = ?, content_hash = ?, indexed_at = datetime('now'), error_message = NULL WHERE id = ?",
                (status, content_hash, doc_id),
            )
        elif error_message:
            await db.execute(
                "UPDATE documents SET status = ?, error_message = ?, indexed_at = NULL WHERE id = ?",
                (status, error_message, doc_id),
            )
        else:
            await db.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, doc_id),
            )
        await db.commit()
        logger.info("Document %d status updated to %s", doc_id, status)

    async def _calculate_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff."""
        return self.base_delay * (self.backoff_multiplier ** retry_count)

    async def _acquire_processing_lock(self, doc_id: int, db: DatabaseConnection) -> bool:
        """Try to acquire lock by transitioning from pending to processing."""
        result = await db.execute(
            "UPDATE documents SET status = 'processing' WHERE id = ? AND status = 'pending'",
            (doc_id,)
        )
        await db.commit()
        return result.rowcount > 0

    async def _process_job(self, job: dict[str, Any]) -> None:
        """Process a single indexing job."""
        payload = job.get("payload", {})
        doc_id = payload.get("document_id")
        user_id = payload.get("user_id")

        if doc_id is None:
            logger.error("Job missing document_id: %s", job)
            return

        db = await self._get_db()

        # Acquire processing lock
        if not await self._acquire_processing_lock(doc_id, db):
            logger.info("Document %d already being processed or not pending, skipping", doc_id)
            return

        try:
            # Validate ownership
            if not await self._validate_ownership(doc_id, user_id, db):
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message="Ownership validation failed",
                    db=db,
                )
                return

            # Get document record to find file path
            doc_record = await db.fetchone(
                "SELECT id, filename, storage_path, content_type FROM documents WHERE id = ?",
                (doc_id,)
            )

            if not doc_record:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message="Document record not found",
                    db=db,
                )
                return

            file_path = doc_record["storage_path"]

            # Extract content
            try:
                content = await self._extract_content(file_path)
            except FileNotFoundError as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=str(e),
                    db=db,
                )
                return
            except Exception as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=f"Failed to extract content: {e}",
                    db=db,
                )
                return

            # Compute content hash
            content_hash = await self._compute_hash(content)

            # Update to indexed status
            await self._update_status(
                doc_id,
                "indexed",
                content_hash=content_hash,
                db=db,
            )

            logger.info("Document %d successfully indexed (hash: %s)", doc_id, content_hash[:16])

        except Exception as e:
            logger.error("Error processing document %d: %s", doc_id, e)
            await self._update_status(
                doc_id,
                "failed",
                error_message=f"Processing error: {e}",
                db=db,
            )

    async def run(self, sleep_interval: float = 0.5) -> None:
        """Main worker loop."""
        logger.info("Starting indexing worker loop")

        try:
            while True:
                job = await job_queue.dequeue()
                if job:
                    await self._process_job(job)
                await asyncio.sleep(sleep_interval)
        except asyncio.CancelledError:
            logger.info("Indexing worker cancelled")

    async def process_single_job(self, job: dict[str, Any]) -> None:
        """Process a single job with retry logic and bounded attempts."""
        payload = job.get("payload", {})
        doc_id = payload.get("document_id")
        retry_count = job.get("retry_count", 0)

        if doc_id is None:
            logger.error("Job missing document_id: %s", job)
            return

        db = await self._get_db()

        # Check if max retries exceeded
        if retry_count >= self.max_retries:
            await self._update_status(
                doc_id,
                "failed",
                error_message=f"Max retries ({self.max_retries}) exceeded",
                db=db,
            )
            logger.error("Document %d failed after %d retries", doc_id, retry_count)
            return

        try:
            await self._process_job(job)
        except Exception as e:
            logger.warning("Document %d processing failed (attempt %d/%d): %s",
                          doc_id, retry_count + 1, self.max_retries, e)

            # Calculate next retry delay
            delay = await self._calculate_delay(retry_count)

            # Re-enqueue with incremented retry count
            job["retry_count"] = retry_count + 1
            job["next_retry_time"] = time.time() + delay

            await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": payload.get("user_id")})
            logger.info("Re-enqueued document %d for retry in %.1f seconds", doc_id, delay)


def get_worker() -> IndexingWorker:
    """Get a new worker instance."""
    return IndexingWorker(max_retries=3)
