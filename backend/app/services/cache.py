"""Redis-backed cache with in-memory fallback."""

import json
import logging
import time
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger("nebula.cache")
settings = get_settings()


class CacheService:
    """Unified cache: Redis when configured, otherwise in-memory."""

    def __init__(self) -> None:
        self._memory: dict[str, tuple[Any, float]] = {}
        self._redis = None

    async def connect(self) -> None:
        if not settings.redis_url:
            return
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis cache connected")
        except Exception as exc:
            logger.warning("Redis unavailable, using in-memory cache: %s", exc)
            self._redis = None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Optional[Any]:
        if self._redis:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        entry = self._memory.get(key)
        if not entry:
            return None
        value, expires = entry
        if time.time() > expires:
            del self._memory[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or settings.cache_ttl_seconds
        if self._redis:
            await self._redis.setex(key, ttl, json.dumps(value))
            return
        self._memory[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        if self._redis:
            await self._redis.delete(key)
        self._memory.pop(key, None)

    async def get_stats(self) -> dict:
        if self._redis:
            info = await self._redis.info()
            return {
                "connected": True,
                "hit_ratio": 0.0,
                "memory_usage_mb": info.get("used_memory", 0) / (1024 * 1024),
                "keys_count": await self._redis.dbsize(),
            }
        return {
            "connected": False,
            "hit_ratio": 0.0,
            "memory_usage_mb": 0.0,
            "keys_count": len(self._memory),
        }

    async def invalidate_prefix(self, prefix: str) -> None:
        await self.invalidate_pattern(prefix)

    async def invalidate_pattern(self, pattern: str) -> None:
        if self._redis:
            keys = [key async for key in self._redis.scan_iter(match=f"{pattern}*")]
            if keys:
                await self._redis.delete(*keys)
            return
        for key in list(self._memory):
            if key.startswith(pattern):
                del self._memory[key]


cache_service = CacheService()
