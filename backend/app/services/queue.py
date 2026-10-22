"""Background job queue with Redis list or in-memory fallback."""

import json
import logging
from collections import deque
from typing import Any

from app.config import get_settings

logger = logging.getLogger("nebula.queue")
settings = get_settings()


class JobQueue:
    def __init__(self) -> None:
        self._queue: deque[dict] = deque()
        self._redis = None
        self._paused = False

    async def connect(self) -> None:
        if not settings.redis_url:
            return
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Job queue connected to Redis")
        except Exception as exc:
            logger.warning("Redis queue unavailable, using in-memory: %s", exc)
            self._redis = None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    async def enqueue(self, job_type: str, payload: dict[str, Any]) -> None:
        job = {"type": job_type, "payload": payload}
        if self._redis:
            await self._redis.rpush("queue:jobs", json.dumps(job))
            return
        self._queue.append(job)
        logger.debug("Enqueued job %s (in-memory)", job_type)

    async def dequeue(self) -> dict | None:
        if self._paused:
            return None
        if self._redis:
            raw = await self._redis.lpop("queue:jobs")
            return json.loads(raw) if raw else None
        return self._queue.popleft() if self._queue else None


job_queue = JobQueue()
