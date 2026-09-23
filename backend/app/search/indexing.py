"""
Background Indexing System

Provides asynchronous document indexing with:
- Job queue management
- Background workers
- Retry mechanism
- Progress tracking
- Failure recovery
- Scheduling
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.config import get_settings
from app.services.cache import cache_service

logger = logging.getLogger("nebula.search.indexing")
settings = get_settings()


class JobStatus(str, Enum):
    """Indexing job status"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(int, Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15


@dataclass
class IndexingJob:
    """Indexing job definition"""
    id: str
    document_id: str
    status: JobStatus
    priority: JobPriority
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None


class BackgroundIndexer:
    """
    Background indexing system with job queue and workers.
    
    Features:
    - Async job processing
    - Priority queue
    - Retry with exponential backoff
    - Progress tracking
    - Failure recovery
    - Concurrent workers
    """

    def __init__(
        self,
        num_workers: int = 4,
        max_queue_size: int = 1000,
        retry_delay_base: float = 1.0,
    ):
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size
        self.retry_delay_base = retry_delay_base
        
        # Job queue (priority queue)
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        
        # Job storage
        self.jobs: Dict[str, IndexingJob] = {}
        
        # Worker tasks
        self.workers: List[asyncio.Task] = []
        
        # Control flags
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "retried_jobs": 0,
        }

    async def start(self):
        """Start background workers"""
        if self.running:
            logger.warning("Background indexer already running")
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} background indexing workers")

    async def stop(self):
        """Stop background workers gracefully"""
        if not self.running:
            return
        
        logger.info("Stopping background indexer...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Background indexer stopped")

    async def submit_job(
        self,
        document_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None,
    ) -> IndexingJob:
        """
        Submit a document for indexing.
        
        Args:
            document_id: Document ID to index
            priority: Job priority
            metadata: Additional metadata
            callback: Optional callback function
            
        Returns:
            IndexingJob instance
        """
        job = IndexingJob(
            id=str(uuid4()),
            document_id=document_id,
            status=JobStatus.QUEUED,
            priority=priority,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {},
            callback=callback,
        )
        
        # Store job
        self.jobs[job.id] = job
        
        # Add to queue (priority queue uses negative priority for max-heap behavior)
        await self.queue.put((-priority.value, job.id))
        
        self.stats["total_jobs"] += 1
        
        logger.debug(f"Submitted indexing job {job.id} for document {document_id}")
        return job

    async def get_job(self, job_id: str) -> Optional[IndexingJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in (JobStatus.PENDING, JobStatus.QUEUED):
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.utcnow()
            logger.info(f"Cancelled job {job_id}")
            return True
        
        return False

    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()

    async def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        return {
            **self.stats,
            "queue_size": await self.get_queue_size(),
            "active_workers": len([w for w in self.workers if not w.done()]),
            "total_jobs_in_memory": len(self.jobs),
        }

    async def _worker(self, worker_name: str):
        """Background worker process"""
        logger.info(f"Worker {worker_name} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get job from queue with timeout
                try:
                    priority, job_id = await asyncio.wait_for(
                        self.queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                job = self.jobs.get(job_id)
                if not job or job.status == JobStatus.CANCELLED:
                    self.queue.task_done()
                    continue
                
                # Process job
                await self._process_job(job, worker_name)
                
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_name} stopped")

    async def _process_job(self, job: IndexingJob, worker_name: str):
        """Process a single indexing job"""
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        
        logger.info(f"Worker {worker_name} processing job {job.id} for document {job.document_id}")
        
        try:
            # Update progress
            job.progress = 0.1
            await self._update_job_progress(job)
            
            # Import here to avoid circular dependencies
            
            # Get document content (would come from database in production)
            # For now, we'll simulate indexing
            job.progress = 0.3
            await self._update_job_progress(job)
            
            # Generate embeddings
            job.progress = 0.5
            await self._update_job_progress(job)
            
            # Store in vector database
            job.progress = 0.8
            await self._update_job_progress(job)
            
            # Mark as completed
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            
            self.stats["completed_jobs"] += 1
            
            logger.info(f"Job {job.id} completed successfully")
            
            # Call callback if provided
            if job.callback:
                try:
                    if asyncio.iscoroutinefunction(job.callback):
                        await job.callback(job)
                    else:
                        job.callback(job)
                except Exception as e:
                    logger.error(f"Callback failed for job {job.id}: {e}")
        
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}", exc_info=True)
            
            # Retry logic
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRYING
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                
                self.stats["retried_jobs"] += 1
                
                # Exponential backoff
                retry_delay = self.retry_delay_base * (2 ** (job.retry_count - 1))
                logger.info(f"Retrying job {job.id} in {retry_delay}s (attempt {job.retry_count})")
                
                await asyncio.sleep(retry_delay)
                
                # Re-queue
                await self.queue.put((-job.priority.value, job.id))
            else:
                # Max retries exceeded
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                
                self.stats["failed_jobs"] += 1
                
                logger.error(f"Job {job.id} failed permanently after {job.retry_count} retries")

    async def _update_job_progress(self, job: IndexingJob):
        """Update job progress in cache"""
        try:
            cache_key = f"indexing:job:{job.id}"
            await cache_service.set(cache_key, {
                "id": job.id,
                "document_id": job.document_id,
                "status": job.status.value,
                "progress": job.progress,
                "updated_at": job.updated_at.isoformat(),
            }, ttl=3600)
        except Exception as e:
            logger.debug(f"Failed to update job progress: {e}")


# Global instance
background_indexer = BackgroundIndexer()


class IndexingManager:
    """High-level indexing management API"""

    def __init__(self):
        self.indexer = background_indexer

    async def start(self):
        """Start indexing system"""
        await self.indexer.start()

    async def stop(self):
        """Stop indexing system"""
        await self.indexer.stop()

    async def index_document(
        self,
        document_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        async_mode: bool = True,
    ) -> IndexingJob:
        """
        Index a document.
        
        Args:
            document_id: Document ID
            priority: Job priority
            async_mode: If True, queue for background processing
            
        Returns:
            IndexingJob instance
        """
        if async_mode:
            return await self.indexer.submit_job(
                document_id=document_id,
                priority=priority,
            )
        else:
            # Synchronous indexing (not recommended for production)
            raise NotImplementedError("Synchronous indexing not implemented")

    async def index_documents_batch(
        self,
        document_ids: List[str],
        priority: JobPriority = JobPriority.NORMAL,
    ) -> List[IndexingJob]:
        """
        Index multiple documents.
        
        Args:
            document_ids: List of document IDs
            priority: Job priority
            
        Returns:
            List of IndexingJob instances
        """
        jobs = []
        for doc_id in document_ids:
            job = await self.indexer.submit_job(
                document_id=doc_id,
                priority=priority,
            )
            jobs.append(job)
        return jobs

    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get indexing job status"""
        job = await self.indexer.get_job(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "document_id": job.document_id,
            "status": job.status.value,
            "progress": job.progress,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }

    async def cancel(self, job_id: str) -> bool:
        """Cancel indexing job"""
        return await self.indexer.cancel_job(job_id)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        return await self.indexer.get_stats()


# Global instance
indexing_manager = IndexingManager()