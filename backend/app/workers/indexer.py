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

    def __init__(self, max_retries: int | None = None) -> None:
        # Use provided max_retries or fall back to configuration
        self.max_retries = max_retries if max_retries is not None else settings.indexing_max_retries
        self.base_delay = settings.indexing_retry_base_delay
        self.backoff_multiplier = settings.indexing_retry_backoff_multiplier
        self._db: DatabaseConnection | None = None

    async def connect(self) -> None:
        """Initialize database connection pool."""
        from app.database import init_db
        await init_db()
        self._db = await get_db()
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
            "SELECT id, user_id, storage_path FROM documents WHERE id = ?",
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

    async def _validate_storage_ownership(self, doc_record: dict, user_id: int) -> bool:
        """Validate that the storage file path belongs to the document owner."""
        db_user_id = doc_record["user_id"]
        storage_path = doc_record["storage_path"]
        
        # Build expected path: storage_uploads/{db_user_id}/{filename}
        expected_path = str(settings.storage_uploads / str(db_user_id) / Path(storage_path).name)
        actual_path = storage_path
        
        # Normalize both paths for comparison
        expected_resolved = Path(expected_path).resolve()
        actual_resolved = Path(actual_path).resolve()
        
        if expected_resolved != actual_resolved:
            logger.warning(
                "Storage path ownership validation failed: expected %s, got %s",
                expected_path, actual_path
            )
            return False
        return True

    async def _sanitize_path(self, storage_path: str) -> Path:
        """Sanitize storage path to prevent path traversal attacks."""
        base_dir = Path(settings.storage_root).resolve() / "uploads"
        
        # Join paths and resolve to get absolute path
        full_path = (base_dir / storage_path).resolve()
        
        # Ensure the resolved path is under base_dir
        try:
            full_path.relative_to(base_dir)
        except ValueError:
            raise PermissionError("Path traversal attempt detected")
        
        return full_path

    async def _validate_file_signature(self, file_path: str, content_type: str | None) -> None:
        """Validate file content signature matches expected type."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read first 1024 bytes for signature check
        with open(path, "rb") as f:
            file_bytes = f.read(1024)
        
        # Check PDF signature
        if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
            if not file_bytes.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF file signature")
        
        # Check DOCX signature (ZIP format)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or path.suffix.lower() == ".docx":
            if not file_bytes.startswith(b"PK\x03\x04"):
                raise ValueError("Invalid DOCX file signature")
        
        # Check plain text (basic heuristic - no binary content)
        elif content_type == "text/plain" or path.suffix.lower() in (".txt", ".md", ".csv", ".json", ".html"):
            try:
                file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # Check for Latin-1 which is common for text files
                try:
                    file_bytes.decode("latin-1")
                except UnicodeDecodeError:
                    raise ValueError("Invalid text file signature - contains binary data")
        
        # No signature check for unknown types - allow processing
        logger.debug("No signature validation for content type: %s", content_type)

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
                "Missing dependency: pypdf. Install with: pip install pypdf"
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
                "Missing dependency: python-docx. Install with: pip install python-docx"
            )

        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)

    def _extract_text(self, path: Path) -> str:
        """Extract text from plain text files (TXT, MD, CSV, JSON, HTML)."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode file with any known encoding: {path}")

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

    async def _calculate_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff."""
        return self.base_delay * (self.backoff_multiplier ** retry_count)

    async def _acquire_processing_lock(self, doc_id: int, db: DatabaseConnection) -> bool:
        """Try to acquire lock by transitioning from pending to processing."""
        result = await db.execute(
            "UPDATE documents SET status = 'processing' WHERE id = ? AND status = 'pending'",
            (doc_id,)
        )
        return result.rowcount > 0

    async def _process_job(self, job: dict[str, Any]) -> None:
        """Process a single indexing job."""
        payload = job.get("payload", {})
        doc_id = payload.get("document_id")
        user_id = payload.get("user_id")

        if doc_id is None:
            logger.error("Job missing document_id: %s", job)
            return

        # Validate user_id is a positive integer
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id in job: %s", user_id)
            # Mark as failed in database
            db = await self._get_db()
            await self._update_status(
                doc_id,
                "failed",
                error_message=f"Invalid user_id in job payload",
                db=db,
            )
            await db.commit()
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
                await db.commit()
                return

            # Get document record to find file path and validate storage ownership
            doc_record = await db.fetchone(
                "SELECT id, filename, storage_path, content_type, user_id FROM documents WHERE id = ?",
                (doc_id,)
            )

            if not doc_record:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message="Document record not found",
                    db=db,
                )
                await db.commit()
                return

            # Validate storage file ownership
            if not await self._validate_storage_ownership(doc_record, user_id):
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message="Storage path ownership validation failed",
                    db=db,
                )
                await db.commit()
                return

            file_path = doc_record["storage_path"]
            
            # Sanitize path to prevent path traversal
            try:
                sanitized_path = await self._sanitize_path(file_path)
            except PermissionError as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=f"Invalid file path: {e}",
                    db=db,
                )
                await db.commit()
                return

            # Re-validate file signatures to ensure file hasn't been modified
            try:
                await self._validate_file_signature(str(sanitized_path), doc_record["content_type"])
            except ValueError as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=f"File signature validation failed: {e}",
                    db=db,
                )
                await db.commit()
                return

            # Extract content
            try:
                content = await self._extract_content(str(sanitized_path))
            except RuntimeError as e:
                # Missing dependency - fail immediately
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=str(e),
                    db=db,
                )
                await db.commit()
                logger.warning("Document %d failed due to missing dependency: %s", doc_id, e)
                return
            except FileNotFoundError as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=str(e),
                    db=db,
                )
                await db.commit()
                return
            except Exception as e:
                await self._update_status(
                    doc_id,
                    "failed",
                    error_message=f"Failed to extract content: {e}",
                    db=db,
                )
                await db.commit()
                return

            # Compute content hash
            content_hash = await self._compute_hash(content)

            # Check for duplicate content (same hash for same user)
            docs = DocumentRepository(db)
            existing = await docs.find_by_hash(user_id, content_hash)
            if existing:
                # Duplicate found - skip indexing but mark as indexed
                await self._update_status(
                    doc_id,
                    "indexed",
                    content_hash=content_hash,
                    db=db,
                )
                await db.commit()
                logger.info(
                    "Document %d is duplicate of %d (hash: %s) - skipping indexing",
                    doc_id, existing["id"], content_hash[:16]
                )
            else:
                # No duplicate - proceed with indexing
                await self._update_status(
                    doc_id,
                    "indexed",
                    content_hash=content_hash,
                    db=db,
                )
                await db.commit()
                logger.info("Document %d successfully indexed (hash: %s)", doc_id, content_hash[:16])

        except Exception as e:
            logger.error("Error processing document %d: %s", doc_id, e)
            await self._update_status(
                doc_id,
                "failed",
                error_message=f"Processing error: {e}",
                db=db,
            )
            await db.commit()

    async def run(self, sleep_interval: float = 0.5) -> None:
        """Main worker loop with job acknowledgment pattern."""
        logger.info("Starting indexing worker loop")

        try:
            while True:
                job = await job_queue.dequeue()
                if job and job.get("type") == "index_document":
                    try:
                        await self._process_job(job)
                        # Job processed successfully - it's acknowledged via document status update
                        # The job was removed from queue, so no further action needed on success
                    except Exception as e:
                        logger.error("Unexpected error processing job: %s", e)
                        # On unexpected error, re-enqueue the job
                        payload = job.get("payload", {})
                        doc_id = payload.get("document_id")
                        if doc_id:
                            # Re-enqueue with current retry count (or 0 if not present)
                            retry_count = max(0, payload.get("retry_count", 0))
                            requeue_payload = {
                                "document_id": doc_id,
                                "user_id": payload.get("user_id"),
                                "retry_count": retry_count + 1,
                                "next_retry_time": time.time(),
                            }
                            await job_queue.enqueue("index_document", requeue_payload)
                            logger.info("Re-enqueued failed job for document %d", doc_id)
                await asyncio.sleep(sleep_interval)
        except asyncio.CancelledError:
            logger.info("Indexing worker cancelled")

    async def process_single_job(self, job: dict[str, Any]) -> None:
        """Process a single job with retry logic and bounded attempts."""
        payload = job.get("payload", {})
        doc_id = payload.get("document_id")
        retry_count = max(0, payload.get("retry_count", 0))

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
            await db.commit()
            logger.error("Document %d failed after %d retries", doc_id, retry_count)
            return

        try:
            await self._process_job(job)
        except RuntimeError as e:
            # Missing dependency - fail immediately
            await self._update_status(
                doc_id,
                "failed",
                error_message=str(e),
                db=db,
            )
            await db.commit()
            logger.warning("Document %d failed due to missing dependency: %s", doc_id, e)
            return
        except Exception as e:
            logger.warning("Document %d processing failed (attempt %d/%d): %s",
                          doc_id, retry_count + 1, self.max_retries, e)

            # Calculate next retry delay
            delay = await self._calculate_delay(retry_count)

            # Re-enqueue with incremented retry count - preserve original payload
            requeue_payload = payload.copy()
            requeue_payload["retry_count"] = retry_count + 1
            requeue_payload["next_retry_time"] = time.time() + delay
            await job_queue.enqueue("index_document", requeue_payload)
            logger.info("Re-enqueued document %d for retry in %.1f seconds", doc_id, delay)


def get_worker() -> IndexingWorker:
    """Get a new worker instance."""
    return IndexingWorker()
