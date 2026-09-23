"""Core indexing services."""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.indexing.config import (
    IndexingStep,
    JobPriority,
    JobStatus,
    get_indexing_config,
)
from app.indexing.metrics import get_metrics_collector
from app.indexing.progress import progress_tracker
from app.indexing.retry import get_retry_handler
from app.indexing.tasks import chunk_text, calculate_file_checksum

logger = logging.getLogger("nebula.indexing.services")
settings = get_settings()


class IndexingService:
    """Core document indexing service."""
    
    def __init__(self) -> None:
        self._config = get_indexing_config()
        self._retry_handler = get_retry_handler()
        self._metrics = get_metrics_collector()
    
    async def index_document(
        self,
        db_session,
        document_id: int,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None,
        priority: str = JobPriority.NORMAL,
    ) -> Dict[str, Any]:
        """
        Index a document.
        
        Args:
            db_session: Database session
            document_id: Document ID
            user_id: User ID
            file_path: Path to document file
            priority: Job priority
            
        Returns:
            Job result dictionary
        """
        job_id = None
        filename = Path(file_path).name if file_path else f"document_{document_id}"
        
        try:
            # Create job in database
            job_id = await self._create_job(
                db_session, document_id, user_id, filename, priority
            )
            
            # Initialize progress
            progress_tracker.create(job_id)
            progress_tracker.update_status(job_id, JobStatus.RUNNING)
            
            # Get file info
            if not file_path or not Path(file_path).exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            file_checksum = calculate_file_checksum(file_path)
            
            # Update job with file info
            await self._update_job(db_session, job_id, {
                "file_size": file_size,
                "file_checksum": file_checksum,
                "started_at": datetime.now().isoformat(),
            })
            
            # Step 1: Extract text
            progress_tracker.update_step(
                job_id, IndexingStep.READING, 10
            )
            text = await self._extract_text(file_path)
            
            # Step 2: Chunk document
            progress_tracker.update_step(
                job_id, IndexingStep.CHUNKING, 30
            )
            chunks = chunk_text(
                text,
                chunk_size=self._config.chunk_size,
                chunk_overlap=self._config.chunk_overlap,
            )
            chunk_count = len(chunks)
            
            # Save chunks
            await self._save_chunks(db_session, document_id, chunks)
            
            # Step 3: Generate embeddings (simplified)
            progress_tracker.update_step(
                job_id, IndexingStep.EMBEDDING, 50
            )
            embeddings = await self._generate_embeddings(chunks)
            embedding_count = len(embeddings)
            
            # Step 4: Store vectors (simplified)
            progress_tracker.update_step(
                job_id, IndexingStep.VECTOR_STORAGE, 75
            )
            await self._store_vectors(document_id, chunks, embeddings)
            
            # Step 5: Finalize
            progress_tracker.update_step(
                job_id, IndexingStep.FINALIZING, 95
            )
            await self._finalize_indexing(
                db_session, job_id, chunk_count, embedding_count
            )
            
            # Complete
            progress_tracker.complete(job_id)
            await self._update_job(db_session, job_id, {
                "status": JobStatus.COMPLETED,
                "progress": 100,
                "completed_at": datetime.now().isoformat(),
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
            })
            
            return {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
            }
            
        except Exception as exc:
            # Handle failure
            error_message = str(exc)
            logger.error("Indexing failed for document %d: %s", document_id, exc)
            
            if job_id:
                progress_tracker.fail(job_id, error_message)
                await self._update_job(db_session, job_id, {
                    "status": JobStatus.FAILED,
                    "error_message": error_message,
                })
            
            self._metrics.record_failure()
            raise
    
    async def _create_job(
        self,
        db_session,
        document_id: int,
        user_id: Optional[int],
        filename: str,
        priority: str,
    ) -> str:
        """Create indexing job in database."""
        job_id = str(__import__("uuid").uuid4())
        
        await db_session.execute(
            """
            INSERT INTO index_jobs
            (job_id, document_id, user_id, filename, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                document_id,
                user_id,
                filename,
                priority,
                JobStatus.QUEUED,
                datetime.now().isoformat(),
            ),
        )
        await db_session.commit()
        
        logger.info("Created indexing job %s for document %d", job_id, document_id)
        return job_id
    
    async def _update_job(
        self,
        db_session,
        job_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """Update job in database."""
        if not updates:
            return
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [job_id]
        
        await db_session.execute(
            f"UPDATE index_jobs SET {set_clause} WHERE job_id = ?",  # nosec B608: set_clause is built from updates dict keys, values are parameterized
            values,
        )
        await db_session.commit()
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from document (placeholder)."""
        ext = Path(file_path).suffix.lower()
        
        if ext == ".txt" or ext == ".md" or ext == ".markdown":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.dumps(json.load(f), indent=2)
        elif ext == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".html":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    async def _save_chunks(
        self,
        db_session,
        document_id: int,
        chunks: List[str],
    ) -> None:
        """Save document chunks to database."""
        for idx, chunk in enumerate(chunks):
            chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()
            
            await db_session.execute(
                """
                INSERT OR REPLACE INTO document_chunks
                (document_id, chunk_id, content, chunk_hash)
                VALUES (?, ?, ?, ?)
                """,
                (document_id, idx, chunk, chunk_hash),
            )
        
        await db_session.commit()
        logger.debug("Saved %d chunks for document %d", len(chunks), document_id)
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for chunks (placeholder)."""
        # This would call the embedding service
        await asyncio.sleep(0.1)  # Simulate embedding generation
        
        # Return dummy embeddings (1536 dims)
        return [[0.0] * 1536 for _ in chunks]
    
    async def _store_vectors(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        """Store vectors in vector database (placeholder)."""
        # This would store embeddings in vector DB
        await asyncio.sleep(0.1)  # Simulate vector storage
        logger.debug("Stored %d vectors for document %d", len(chunks), document_id)
    
    async def _finalize_indexing(
        self,
        db_session,
        job_id: str,
        chunk_count: int,
        embedding_count: int,
    ) -> None:
        """Finalize indexing."""
        duration = datetime.now().isoformat()
        
        await self._update_job(db_session, job_id, {
            "completed_at": duration,
            "duration": (datetime.now() - datetime.now()).total_seconds(),
        })
        
        self._metrics.record_indexed_document(0, chunk_count)
        logger.info("Indexing completed for job %s", job_id)


# Global service instance
indexing_service = IndexingService()


def get_indexing_service() -> IndexingService:
    """Get global indexing service."""
    return indexing_service