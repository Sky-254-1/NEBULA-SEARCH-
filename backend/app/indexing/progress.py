"""Progress tracking for indexing jobs."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.indexing.config import IndexingStep

logger = logging.getLogger("nebula.indexing.progress")


@dataclass
class JobProgress:
    """Tracks progress of a single indexing job."""
    job_id: str
    status: str
    progress: int  # 0-100
    current_step: Optional[IndexingStep] = None
    started_at: Optional[float] = None
    last_update: Optional[float] = None
    worker_id: Optional[str] = None
    document_size: Optional[int] = None
    chunks_processed: int = 0
    total_chunks: int = 0
    embeddings_processed: int = 0
    error_message: Optional[str] = None
    
    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.started_at:
            return time.time() - self.started_at
        return None
    
    @property
    def eta_seconds(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if not self.started_at or self.progress <= 0 or self.progress >= 100:
            return None
        
        elapsed = time.time() - self.started_at
        rate = self.progress / elapsed  # percent per second
        remaining = 100 - self.progress
        
        if rate > 0:
            return remaining / rate
        return None
    
    @property
    def speed(self) -> Optional[str]:
        """Get processing speed as human-readable string."""
        if not self.started_at or self.chunks_processed == 0:
            return None
        
        elapsed = time.time() - self.started_at
        if elapsed <= 0:
            return None
        
        chunks_per_second = self.chunks_processed / elapsed
        
        if chunks_per_second >= 1:
            return f"{chunks_per_second:.1f} chunks/sec"
        else:
            seconds_per_chunk = 1 / chunks_per_second
            return f"{seconds_per_chunk:.1f} sec/chunk"
    
    def update_step(self, step: str | IndexingStep, progress: int) -> None:
        """Update current step and progress."""
        # Handle both string and IndexingStep inputs
        if isinstance(step, str):
            try:
                self.current_step = IndexingStep(step)
            except ValueError:
                self.current_step = None
        else:
            self.current_step = step
        self.progress = progress
        self.last_update = time.time()
        step_name = step.value if isinstance(step, IndexingStep) else step
        logger.debug("Job %s: %s at %d%%", self.job_id, step_name, progress)
    
    def increment_progress(self, amount: int) -> None:
        """Increment progress by amount."""
        self.progress = min(100, self.progress + amount)
        self.last_update = time.time()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step.value if self.current_step else None,
            "eta_seconds": self.eta_seconds,
            "speed": self.speed,
            "elapsed_seconds": self.elapsed_seconds,
            "worker_id": self.worker_id,
        }


class ProgressTracker:
    """Tracks progress for all indexing jobs."""
    
    def __init__(self) -> None:
        self._progress_map: dict[str, JobProgress] = {}
    
    def create(self, job_id: str, document_size: Optional[int] = None) -> JobProgress:
        """Create new progress tracker for job."""
        progress = JobProgress(
            job_id=job_id,
            status="QUEUED",
            progress=0,
            document_size=document_size,
        )
        self._progress_map[job_id] = progress
        return progress
    
    def get(self, job_id: str) -> Optional[JobProgress]:
        """Get progress for job."""
        return self._progress_map.get(job_id)
    
    def update_status(self, job_id: str, status: str) -> None:
        """Update job status."""
        progress = self._progress_map.get(job_id)
        if progress:
            progress.status = status
            if status == "RUNNING" and not progress.started_at:
                progress.started_at = time.time()
            progress.last_update = time.time()
    
    def start(self, job_id: str, worker_id: str) -> None:
        """Mark job as started."""
        progress = self._progress_map.get(job_id)
        if progress:
            progress.status = "RUNNING"
            progress.started_at = time.time()
            progress.worker_id = worker_id
            progress.last_update = time.time()
    
    def complete(self, job_id: str) -> None:
        """Mark job as completed."""
        progress = self._progress_map.get(job_id)
        if progress:
            progress.status = "COMPLETED"
            progress.progress = 100
            progress.current_step = None
            progress.last_update = time.time()
    
    def fail(self, job_id: str, error_message: str) -> None:
        """Mark job as failed."""
        progress = self._progress_map.get(job_id)
        if progress:
            progress.status = "FAILED"
            progress.error_message = error_message
            progress.last_update = time.time()
    
    def cancel(self, job_id: str) -> None:
        """Mark job as cancelled."""
        progress = self._progress_map.get(job_id)
        if progress:
            progress.status = "CANCELLED"
            progress.last_update = time.time()
    
    def remove(self, job_id: str) -> None:
        """Remove job from tracker."""
        self._progress_map.pop(job_id, None)
    
    def get_all(self) -> dict[str, JobProgress]:
        """Get all job progress."""
        return self._progress_map.copy()


# Global progress tracker instance
progress_tracker = ProgressTracker()