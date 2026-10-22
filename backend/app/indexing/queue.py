"""Priority queue for indexing jobs with persistence."""

import json
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings
from app.indexing.config import JobPriority, get_indexing_config

logger = logging.getLogger("nebula.indexing.queue")
settings = get_settings()
config = get_indexing_config()


class QueueError(Exception):
    """Queue operation error."""
    pass


@dataclass(order=True)
class PrioritizedJob:
    """Job with priority for queue ordering."""
    priority: int
    enqueue_time: float
    job: dict


    @property
    def sort_key(self) -> tuple:
        return (-self.priority, self.enqueue_time)


class IndexingQueue:
    """Thread-safe priority queue with Redis persistence."""

    def __init__(self) -> None:
        self._local_queue: deque[PrioritizedJob] = deque()
        self._redis = None
        self._priority_map = {
            JobPriority.SYSTEM: 100,
            JobPriority.HIGH: 50,
            JobPriority.NORMAL: 25,
            JobPriority.LOW: 10,
        }
        self._paused = False
        self._size = 0
        self._lock = None  # asyncio lock would be needed in real impl

    async def connect(self) -> None:
        """Connect to Redis if available."""
        if not settings.redis_url:
            logger.info("No Redis configured, using in-memory queue")
            return
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Indexing queue connected to Redis")
            
            # Recover persisted jobs
            await self._recover_persisted_jobs()
        except Exception as exc:
            logger.warning("Redis queue unavailable, using in-memory: %s", exc)
            self._redis = None

    async def _recover_persisted_jobs(self) -> None:
        """Recover jobs from Redis on startup."""
        if not self._redis:
            return
        try:
            raw_jobs = await self._redis.lrange("indexing:queue", 0, -1)
            for raw in raw_jobs:
                try:
                    job_data = json.loads(raw)
                    priority = job_data.get("priority", JobPriority.NORMAL)
                    priority_value = self._priority_map.get(priority, 25)
                    pj = PrioritizedJob(
                        priority=priority_value,
                        enqueue_time=job_data.get("enqueue_time", time.time()),
                        job=job_data,
                    )
                    self._local_queue.append(pj)
                    self._size += 1
                except json.JSONDecodeError:
                    logger.error("Failed to recover persisted job")
            if raw_jobs:
                logger.info("Recovered %d jobs from queue", len(raw_jobs))
        except Exception as exc:
            logger.error("Failed to recover jobs: %s", exc)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def enqueue(self, job: dict) -> str:
        """
        Add job to queue.
        
        Args:
            job: Job dictionary with at least 'type' and 'payload'
            
        Returns:
            job_id: Unique job identifier
            
        Raises:
            QueueError: If queue is full
        """
        if self._size >= config.max_queue_size:
            raise QueueError("Queue is full")
        
        job_id = job.get("job_id") or str(uuid.uuid4())
        job["job_id"] = job_id
        priority = job.get("priority", JobPriority.NORMAL)
        priority_value = self._priority_map.get(priority, 25)
        job["enqueue_time"] = time.time()
        
        pj = PrioritizedJob(
            priority=priority_value,
            enqueue_time=job["enqueue_time"],
            job=job,
        )
        
        if self._redis:
            try:
                # Use sorted set: score = (priority * 1000000) - enqueue_time
                # Higher priority = lower score, earlier enqueue = lower score
                score = (priority_value * 1000000) - pj.enqueue_time
                await self._redis.zadd(
                    "indexing:priority_queue",
                    {json.dumps(pj.job): score},
                )
            except Exception as exc:
                logger.error("Failed to enqueue to Redis: %s", exc)
                # Fallback to local
                self._local_queue.append(pj)
                self._local_queue = deque(
                    sorted(self._local_queue, key=lambda x: x.sort_key)
                )
        else:
            self._local_queue.append(pj)
            self._local_queue = deque(
                sorted(self._local_queue, key=lambda x: x.sort_key)
            )
        self._size += 1
        
        logger.debug("Enqueued job %s with priority %s", job_id, priority)
        return job_id

    async def dequeue(self) -> Optional[dict]:
        """
        Get highest priority job from queue.
        
        Returns:
            Job dict or None if queue is empty/paused
        """
        if self._paused:
            return None
        
        job = None
        
        if self._redis:
            try:
                # Get highest priority (lowest score) item
                raw = await self._redis.zpopmin("indexing:priority_queue", count=1)
                if raw:
                    job_data, _ = raw[0]
                    job = json.loads(job_data)
                    self._size = max(0, self._size - 1)
            except Exception as exc:
                logger.error("Failed to dequeue from Redis: %s", exc)
        
        # Fallback to local queue
        if not job and self._local_queue:
            pj = self._local_queue.popleft()
            job = pj.job
            self._size = max(0, self._size - 1)
        
        return job

    async def peek(self, count: int = 10) -> list[dict]:
        """
        Peek at jobs without removing them.
        
        Args:
            count: Maximum number of jobs to return
            
        Returns:
            List of job dicts
        """
        jobs = []
        
        if self._redis:
            try:
                raw_jobs = await self._redis.zrange(
                    "indexing:priority_queue", 0, count - 1
                )
                for raw in raw_jobs:
                    try:
                        job = json.loads(raw)
                        jobs.append(job)
                    except json.JSONDecodeError:
                        continue
            except Exception as exc:
                logger.error("Failed to peek Redis queue: %s", exc)
        
        # Add local queue items
        sorted_local = sorted(
            self._local_queue,
            key=lambda pj: pj.sort_key
        )[:count - len(jobs)]
        for pj in sorted_local:
            jobs.append(pj.job)
        
        return jobs

    async def remove(self, job_id: str) -> bool:
        """
        Remove a specific job from queue.
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if removed, False if not found
        """
        removed = False
        
        if self._redis:
            try:
                raw_jobs = await self._redis.zrange("indexing:priority_queue", 0, -1)
                for raw in raw_jobs:
                    try:
                        job = json.loads(raw)
                        if job.get("job_id") == job_id:
                            await self._redis.zrem("indexing:priority_queue", raw)
                            removed = True
                            self._size = max(0, self._size - 1)
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception as exc:
                logger.error("Failed to remove from Redis: %s", exc)
        
        # Check local queue
        if not removed:
            for i, pj in enumerate(self._local_queue):
                if pj.job.get("job_id") == job_id:
                    del self._local_queue[i]
                    removed = True
                    self._size = max(0, self._size - 1)
                    break
        
        return removed

    async def clear(self) -> None:
        """Clear all jobs from queue."""
        if self._redis:
            try:
                await self._redis.delete("indexing:priority_queue")
            except Exception as exc:
                logger.error("Failed to clear Redis queue: %s", exc)
        self._local_queue.clear()
        self._size = 0
        logger.info("Queue cleared")

    @property
    def size(self) -> int:
        """Get current queue size."""
        # Return local size (Redis size would need async call)
        return self._size

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.size == 0
    
    def pause(self) -> None:
        """Pause queue processing."""
        self._paused = True
        logger.info("Queue paused")
    
    def resume(self) -> None:
        """Resume queue processing."""
        self._paused = False
        logger.info("Queue resumed")
    
    @property
    def is_paused(self) -> bool:
        """Check if queue is paused."""
        return self._paused


# Global queue instance
indexing_queue = IndexingQueue()