"""Dead-letter queue for failed indexing jobs."""

import logging
from datetime import datetime
from typing import Optional


logger = logging.getLogger("nebula.indexing.deadletter")


class DeadLetterQueue:
    """Manages failed jobs that exceeded max retries."""
    
    def __init__(self, db_session):
        """
        Initialize dead-letter queue.
        
        Args:
            db_session: Database session (async)
        """
        self._db = db_session
    
    async def add(
        self,
        job_id: str,
        document_id: int,
        filename: str,
        failure_reason: str,
        retries: int,
        worker_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """
        Add failed job to dead-letter queue.
        
        Args:
            job_id: Job identifier
            document_id: Document identifier
            filename: Document filename
            failure_reason: Reason for failure
            retries: Number of retries attempted
            worker_id: Worker that failed
            stack_trace: Stack trace of error
        """
        try:
            await self._db.execute(
                """
                INSERT INTO dead_letter_queue
                (job_id, document_id, filename, failure_reason, retries, failed_at, worker_id, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    document_id,
                    filename,
                    failure_reason,
                    retries,
                    datetime.now().isoformat(),
                    worker_id,
                    stack_trace,
                ),
            )
            await self._db.commit()
            logger.error(
                "Job %s moved to dead-letter queue: %s (retries: %d)",
                job_id, failure_reason, retries,
            )
        except Exception as exc:
            logger.error("Failed to add job to dead-letter queue: %s", exc)
    
    async def remove(self, job_id: str) -> bool:
        """
        Remove job from dead-letter queue.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if removed, False if not found
        """
        try:
            result = await self._db.execute(
                "DELETE FROM dead_letter_queue WHERE job_id = ?",
                (job_id,),
            )
            await self._db.commit()
            return result.rowcount > 0
        except Exception as exc:
            logger.error("Failed to remove job from dead-letter queue: %s", exc)
            return False
    
    async def get(self, job_id: str) -> Optional[dict]:
        """
        Get job from dead-letter queue.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job dict or None
        """
        try:
            cursor = await self._db.execute(
                "SELECT * FROM dead_letter_queue WHERE job_id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as exc:
            logger.error("Failed to get job from dead-letter queue: %s", exc)
            return None
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        List all jobs in dead-letter queue.
        
        Args:
            limit: Maximum number of jobs to return
            offset: Offset for pagination
            
        Returns:
            List of job dicts
        """
        try:
            cursor = await self._db.execute(
                """
                SELECT * FROM dead_letter_queue
                ORDER BY failed_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to list dead-letter queue: %s", exc)
            return []
    
    async def count(self) -> int:
        """Get count of jobs in dead-letter queue."""
        try:
            cursor = await self._db.execute(
                "SELECT COUNT(*) as count FROM dead_letter_queue"
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        except Exception as exc:
            logger.error("Failed to count dead-letter queue: %s", exc)
            return 0
    
    async def clear(self, older_than_days: int = 30) -> int:
        """
        Clear old jobs from dead-letter queue.
        
        Args:
            older_than_days: Remove jobs older than this many days
            
        Returns:
            Number of jobs removed
        """
        try:
            cutoff = datetime.now() - datetime.timedelta(days=older_than_days)
            result = await self._db.execute(
                "DELETE FROM dead_letter_queue WHERE failed_at < ?",
                (cutoff.isoformat(),),
            )
            await self._db.commit()
            count = result.rowcount
            logger.info("Cleared %d jobs from dead-letter queue", count)
            return count
        except Exception as exc:
            logger.error("Failed to clear dead-letter queue: %s", exc)
            return 0


def get_dead_letter_queue(db_session) -> DeadLetterQueue:
    """Get dead-letter queue instance."""
    return DeadLetterQueue(db_session)