"""Background workers for indexing jobs."""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.config import get_settings
from app.indexing.config import (
    get_indexing_config,
)
from app.indexing.deadletter import get_dead_letter_queue
from app.indexing.health import get_worker_health_monitor
from app.indexing.metrics import get_metrics_collector
from app.indexing.progress import progress_tracker
from app.indexing.queue import indexing_queue
from app.indexing.retry import get_retry_handler

logger = logging.getLogger("nebula.indexing.worker")
settings = get_settings()


class Worker:
    """Background worker that processes indexing jobs."""
    
    def __init__(self, worker_id: Optional[str] = None) -> None:
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self._running = False
        self._current_job: Optional[Dict[str, Any]] = None
        self._job_start_time: Optional[float] = None
        self._task: Optional[asyncio.Task] = None
        self._processor: Optional[Callable] = None
    
    async def start(
        self,
        processor: Optional[Callable] = None,
        worker_count: int = 1,
    ) -> None:
        """
        Start the worker.
        
        Args:
            processor: Job processing function
            worker_count: Number of concurrent jobs this worker handles
        """
        self._processor = processor
        self._running = True
        
        # Register with health monitor
        health_monitor = get_worker_health_monitor()
        health_monitor.register_worker(self.worker_id)
        
        logger.info("Worker started: %s", self.worker_id)
    
    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Unregister from health monitor
        health_monitor = get_worker_health_monitor()
        health_monitor.unregister_worker(self.worker_id)
        
        logger.info("Worker stopped: %s", self.worker_id)
    
    async def run_once(self) -> None:
        """Process a single job from the queue."""
        if not self._running:
            return
        
        try:
            # Dequeue job
            job = await indexing_queue.dequeue()
            if not job:
                return
            
            # Mark as started
            job_id = job["job_id"]
            progress_tracker.update_status(job_id, "RUNNING")
            progress_tracker.start(job_id, self.worker_id)
            
            # Update health
            health_monitor = get_worker_health_monitor()
            health_monitor.update_status(self.worker_id, "BUSY", job_id)
            health_monitor.heartbeat(self.worker_id)
            
            self._job_start_time = time.time()
            
            # Process job
            try:
                if self._processor:
                    await self._processor(job)
                else:
                    await self._default_processor(job)
                
                # Mark complete
                duration = time.time() - self._job_start_time
                progress_tracker.complete(job_id)
                
                # Record metrics
                metrics = get_metrics_collector()
                metrics.record_indexed_document(duration)
                health_monitor.record_job_completion(self.worker_id, duration, success=True)
                
            except Exception as exc:
                # Job failed
                duration = time.time() - self._job_start_time if self._job_start_time else 0
                progress_tracker.fail(job_id, str(exc))
                
                # Record metrics
                metrics = get_metrics_collector()
                metrics.record_failure()
                health_monitor.record_job_completion(self.worker_id, duration, success=False)
                
                # Handle retries
                retry_handler = get_retry_handler()
                retry_count = job.get("retry_count", 0)
                
                if retry_handler.should_retry(exc, retry_count):
                    logger.warning(
                        "Job %s failed, scheduling retry (attempt %d): %s",
                        job_id, retry_count + 1, str(exc),
                    )
                    
                    # Increment retry count
                    job["retry_count"] = retry_count + 1
                    job["error"] = str(exc)
                    
                    # Calculate delay
                    delay = retry_handler.get_delay(retry_count)
                    job["next_retry_time"] = time.time() + delay
                    
                    # Re-enqueue with delay
                    await indexing_queue.enqueue(job)
                    progress_tracker.update_status(job_id, "RETRYING")
                    metrics.record_retry()
                
                else:
                    # Move to dead-letter queue
                    logger.error(
                        "Job %s failed permanently after %d retries: %s",
                        job_id, retry_count, str(exc),
                    )
                    
                    dead_letter = get_dead_letter_queue(None)
                    await dead_letter.add(
                        job_id=job_id,
                        document_id=job.get("document_id", 0),
                        filename=job.get("filename", ""),
                        failure_reason=str(exc),
                        retries=retry_count,
                        worker_id=self.worker_id,
                    )
            
            finally:
                self._current_job = None
                self._job_start_time = None
                health_monitor.update_status(self.worker_id, "IDLE")
                health_monitor.heartbeat(self.worker_id)
        
        except Exception as exc:
            logger.error("Worker error: %s", exc)
    
    async def _default_processor(self, job: Dict[str, Any]) -> None:
        """
        Default job processor (placeholder).
        
        Args:
            job: Job dictionary
        """
        job_type = job.get("type")
        payload = job.get("payload", {})
        
        logger.info("Processing job %s of type %s", job["job_id"], job_type)
        
        if job_type == "index_document":
            await self._process_document_indexing(payload)
        else:
            logger.warning("Unknown job type: %s", job_type)
    
    async def _process_document_indexing(self, payload: Dict[str, Any]) -> None:
        """
        Process document indexing (minimal stub).
        
        Args:
            payload: Job payload
        """
        document_id = payload.get("document_id")
        payload.get("user_id")
        filename = payload.get("filename", "")
        file_path = payload.get("file_path")
        
        logger.info("Indexing document %d (%s)", document_id, filename)
        
        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        # Read file
        progress_tracker.update_step("document has no real processor; mock behavior only", 0)


class WorkerPool:
    """Manages a pool of workers."""
    
    def __init__(self, worker_count: int = 2) -> None:
        self._worker_count = worker_count
        self._workers: list[Worker] = []
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start all workers."""
        if self._running:
            return
        
        self._running = True
        
        # Create workers
        for _ in range(self._worker_count):
            worker = Worker()
            await worker.start()
            self._workers.append(worker)
        
        # Start processing loop
        self._loop_task = asyncio.create_task(self._process_loop())
        
        logger.info("Worker pool started with %d workers", self._worker_count)
    
    async def stop(self) -> None:
        """Stop all workers."""
        self._running = False
        
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        
        for worker in self._workers:
            await worker.stop()
        
        self._workers.clear()
        logger.info("Worker pool stopped")
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            for worker in self._workers:
                if not worker._running:
                    continue
                try:
                    await worker.run_once()
                except Exception as exc:
                    logger.error("Worker %s error: %s", worker.worker_id, exc)
            
            # Small sleep to prevent busy loop
            await asyncio.sleep(0.5)
    
    def get_worker_count(self) -> int:
        """Get number of active workers."""
        return len([w for w in self._workers if w._running])


# Global worker pool
worker_pool: Optional[WorkerPool] = None


def get_worker_pool() -> WorkerPool:
    """Get global worker pool."""
    global worker_pool
    if worker_pool is None:
        config = get_indexing_config()
        worker_pool = WorkerPool(worker_count=config.worker_count)
    return worker_pool