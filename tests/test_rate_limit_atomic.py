"""Regression tests for sliding-window rate limiting under concurrency."""

import asyncio
import importlib

import pytest

from app.middleware.rate_limit import RateLimiter

rate_limit_module = importlib.import_module("app.middleware.rate_limit")


@pytest.mark.asyncio
async def test_memory_window_counts_simultaneous_requests_with_same_timestamp():
    limiter = RateLimiter()
    decisions = await asyncio.gather(
        *(limiter._check_sliding_window("shared", 7, 60, 100.0) for _ in range(40))
    )

    assert sum(allowed for allowed, _ in decisions) == 7
    assert len(limiter._memory_store["mem:shared"]) == 7


@pytest.mark.asyncio
async def test_memory_window_expires_event_at_window_boundary():
    limiter = RateLimiter()
    assert (await limiter._check_sliding_window("boundary", 1, 10, 100.0))[0]
    allowed, info = await limiter._check_sliding_window("boundary", 1, 10, 110.0)

    assert allowed
    assert info["remaining"] == 0
    assert len(limiter._memory_store["mem:boundary"]) == 1


@pytest.mark.asyncio
async def test_memory_limit_boundary_and_nonpositive_limit():
    limiter = RateLimiter()
    assert (await limiter._check_sliding_window("limit", 2, 30, 10.0))[0]
    assert (await limiter._check_sliding_window("limit", 2, 30, 10.0))[0]
    allowed, info = await limiter._check_sliding_window("limit", 2, 30, 10.0)
    assert not allowed
    assert info["retry_after"] > 0
    assert not (await limiter._check_sliding_window("zero", 0, 30, 10.0))[0]


@pytest.mark.asyncio
async def test_memory_store_evicts_old_keys_when_bounded():
    limiter = RateLimiter()
    limiter._max_memory_keys = 2
    for key, now in (("a", 1.0), ("b", 2.0), ("c", 3.0)):
        assert (await limiter._check_sliding_window(key, 1, 60, now))[0]
    assert len(limiter._memory_store) == 2
    assert "mem:a" not in limiter._memory_store


@pytest.mark.asyncio
async def test_redis_uses_atomic_script_and_unique_members(monkeypatch):
    class AtomicRedis:
        def __init__(self):
            self.members = set()
            self.calls = []

        async def eval(self, script, key_count, key, window, limit, member):
            self.calls.append((script, key_count, key, window, limit, member))
            self.members.add(member)
            count = len(self.members)
            return [int(count <= limit), count if count <= limit else count - 1,
                    10 if count > limit else 0, 110]

    redis = AtomicRedis()
    monkeypatch.setattr(rate_limit_module.cache_service, "_redis", redis)
    limiter = RateLimiter()
    outcomes = await asyncio.gather(*(
        limiter._check_sliding_window("redis", 1, 10, 100.0) for _ in range(2)
    ))

    assert sum(allowed for allowed, _ in outcomes) == 1
    assert len(redis.members) == 2
    assert all(call[1] == 1 and "ZREMRANGEBYSCORE" in call[0] for call in redis.calls)
