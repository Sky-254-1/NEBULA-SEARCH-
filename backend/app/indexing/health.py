"""Health monitoring for indexing workers."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("nebula.indexing.health")


@dataclass
class WorkerHealth:
    """Health status of a single worker."""
    worker_id: str
    status: str  # IDLE, BUSY, DEAD, STOPPED
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    current_job_id: Optional[str] = None
    processed_jobs: int = 0
    failed_jobs: int = 0
    average_duration: float = 0.0
    total_duration: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


class WorkerHealthMonitor:
    """Monitors health of all indexing workers."""
    
    def __init__(self) -> None:
        self._workers: dict[str, WorkerHealth] = {}
        self._heartbeat_timeout = 60.0  # seconds
        self._restart_callback = None
    
    def register_worker(self, worker_id: Optional[str] = None) -> str:
        """
        Register a new worker.
        
        Args:
            worker_id: Optional worker ID (generated if not provided)
            
        Returns:
            Worker ID
        """
        worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        health = WorkerHealth(worker_id=worker_id, status="IDLE")
        self._workers[worker_id] = health
        logger.info("Worker registered: %s", worker_id)
        return worker_id
    
    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker."""
        if worker_id in self._workers:
            self._workers[worker_id].status = "STOPPED"
            logger.info("Worker unregistered: %s", worker_id)
    
    def heartbeat(self, worker_id: str) -> None:
        """Record heartbeat from worker."""
        if worker_id in self._workers:
            self._workers[worker_id].last_heartbeat = time.time()
    
    def update_status(self, worker_id: str, status: str, job_id: Optional[str] = None) -> None:
        """
        Update worker status.
        
        Args:
            worker_id: Worker identifier
            status: New status (IDLE, BUSY, DEAD, STOPPED)
            job_id: Current job ID if BUSY
        """
        if worker_id in self._workers:
            health = self._workers[worker_id]
            health.status = status
            health.current_job_id = job_id
            health.last_heartbeat = time.time()
            
            if status == "BUSY":
                logger.debug("Worker %s is now busy with job %s", worker_id, job_id)
            else:
                logger.debug("Worker %s is now %s", worker_id, status)
    
    def record_job_completion(self, worker_id: str, duration: float, success: bool) -> None:
        """
        Record job completion.
        
        Args:
            worker_id: Worker identifier
            duration: Job duration in seconds
            success: Whether job succeeded
        """
        if worker_id not in self._workers:
            return
        
        health = self._workers[worker_id]
        health.processed_jobs += 1
        
        if not success:
            health.failed_jobs += 1
        
        # Update average duration
        health.total_duration += duration
        health.average_duration = health.total_duration / health.processed_jobs
        
        logger.debug(
            "Worker %s completed job (success=%s, duration=%.2f, avg=%.2f)",
            worker_id, success, duration, health.average_duration,
        )
    
    def get_worker(self, worker_id: str) -> Optional[WorkerHealth]:
        """Get health status for specific worker."""
        return self._workers.get(worker_id)
    
    def get_all_workers(self) -> dict[str, WorkerHealth]:
        """Get all worker health statuses."""
        return self._workers.copy()
    
    def get_active_workers(self) -> dict[str, WorkerHealth]:
        """Get active (non-dead, non-stopped) workers."""
        return {
            wid: health
            for wid, health in self._workers.items()
            if health.status in ("IDLE", "BUSY")
        }
    
    def check_dead_workers(self) -> list[str]:
        """
        Check for dead workers (no recent heartbeat).
        
        Returns:
            List of dead worker IDs
        """
        now = time.time()
        dead_workers = []
        
        for worker_id, health in self._workers.items():
            if health.status in ("STOPPED", "DEAD"):
                continue
            
            time_since_heartbeat = now - health.last_heartbeat
            if time_since_heartbeat > self._heartbeat_timeout:
                health.status = "DEAD"
                dead_workers.append(worker_id)
                logger.warning(
                    "Worker %s marked as DEAD (no heartbeat for %.1f seconds)",
                    worker_id,
                    time_since_heartbeat,
                )
        
        return dead_workers
    
    async def restart_dead_workers(self) -> None:
        """Restart dead workers if callback is configured."""
        dead_workers = self.check_dead_workers()
        
        for worker_id in dead_workers:
            logger.warning("Attempting to restart dead worker: %s", worker_id)
            
            # Reset worker status
            if worker_id in self._workers:
                self._workers[worker_id].status = "IDLE"
                self._workers[worker_id].current_job_id = None
                self._workers[worker_id].last_heartbeat = time.time()
            
            # Call restart callback if configured
            if self._restart_callback:
                try:
                    await self._restart_callback(worker_id)
                except Exception as exc:
                    logger.error("Failed to restart worker %s: %s", worker_id, exc)
    
    def set_restart_callback(self, callback) -> None:
        """Set callback for worker restart."""
        self._restart_callback = callback
    
    def get_statistics(self) -> dict:
        """Get worker pool statistics."""
        all_workers = self.get_all_workers()
        active = self.get_active_workers()
        
        total_processed = sum(w.processed_jobs for w in all_workers.values())
        total_failed = sum(w.failed_jobs for w in all_workers.values())
        
        avg_duration = 0.0
        if total_processed > 0:
            avg_duration = sum(w.average_duration for w in active.values()) / max(len(active), 1)
        
        return {
            "total_workers": len(all_workers),
            "active_workers": len(active),
            "idle_workers": sum(1 for w in active.values() if w.status == "IDLE"),
            "busy_workers": sum(1 for w in active.values() if w.status == "BUSY"),
            "dead_workers": sum(1 for w in all_workers.values() if w.status == "DEAD"),
            "total_processed_jobs": total_processed,
            "total_failed_jobs": total_failed,
            "average_duration": avg_duration,
        }
    
    def to_response_dict(self) -> list[dict]:
        """Convert workers to response format."""
        return [
            {
                "worker_id": health.worker_id,
                "status": health.status,
                "cpu_usage": health.cpu_usage,
                "memory_usage": health.memory_usage,
                "current_job_id": health.current_job_id,
                "processed_jobs": health.processed_jobs,
                "failed_jobs": health.failed_jobs,
                "average_duration": health.average_duration,
                "heartbeat": datetime.fromtimestamp(health.last_heartbeat).isoformat(),
            }
            for health in self._workers.values()
        ]


# Global health monitor
worker_health_monitor = WorkerHealthMonitor()


def get_worker_health_monitor() -> WorkerHealthMonitor:
    """Get global worker health monitor."""
    return worker_health_monitor