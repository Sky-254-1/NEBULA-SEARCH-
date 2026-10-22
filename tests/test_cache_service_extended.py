"""Extended tests for CacheService."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cache import CacheService

@pytest.mark.asyncio
async def test_cache_service_memory_fallback():
    # Patch the settings used inside CacheService methods
    with patch("app.services.cache.settings") as mocked_settings:
        mocked_settings.redis_url = None
        mocked_settings.cache_ttl_seconds = 60

        cache = CacheService()
        await cache.connect()
        assert cache._redis is None

        # Test basic set/get
        await cache.set("foo", "bar", ttl=10)
        assert await cache.get("foo") == "bar"

        # Test TTL
        with patch("app.services.cache.time.time") as mock_time:
            now = 1000.0
            mock_time.return_value = now
            await cache.set("ttl_key", "value", ttl=5)
            # expires at 1005.0

            mock_time.return_value = 1001.0
            assert await cache.get("ttl_key") == "value"

            mock_time.return_value = 1006.0
            assert await cache.get("ttl_key") is None

        await cache.set("foo", "bar")
        await cache.delete("foo")
        assert await cache.get("foo") is None

@pytest.mark.asyncio
async def test_cache_service_redis_success():
    with patch("app.services.cache.settings") as mocked_settings:
        mocked_settings.redis_url = "redis://localhost"
        mocked_settings.cache_ttl_seconds = 60

        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            cache = CacheService()
            await cache.connect()
            assert cache._redis is not None

            await cache.set("foo", {"a": 1})
            mock_redis_client.setex.assert_called_once()

            mock_redis_client.get.return_value = '{"a": 1}'
            assert await cache.get("foo") == {"a": 1}

            await cache.delete("foo")
            mock_redis_client.delete.assert_called_with("foo")

            await cache.close()
            mock_redis_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_cache_service_redis_failure_fallback():
    with patch("app.services.cache.settings") as mocked_settings:
        mocked_settings.redis_url = "redis://localhost"

        with patch("redis.asyncio.from_url", side_effect=Exception("Connection failed")):
            cache = CacheService()
            await cache.connect()
            assert cache._redis is None

@pytest.mark.asyncio
async def test_cache_service_invalidate_prefix_memory():
    with patch("app.services.cache.settings") as mocked_settings:
        mocked_settings.redis_url = None
        mocked_settings.cache_ttl_seconds = 60
        cache = CacheService()
        await cache.set("user:1", "data1")
        await cache.set("user:2", "data2")
        await cache.set("other:1", "data3")

        await cache.invalidate_prefix("user:")
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("other:1") == "data3"

@pytest.mark.asyncio
async def test_cache_service_invalidate_prefix_redis():
    with patch("app.services.cache.settings") as mocked_settings:
        mocked_settings.redis_url = "redis://localhost"
        mock_redis_client = AsyncMock()

        async def mock_scan_iter(match=None):
            yield "user:1"
            yield "user:2"

        mock_redis_client.scan_iter = MagicMock(return_value=mock_scan_iter())

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            cache = CacheService()
            await cache.connect()
            await cache.invalidate_prefix("user:")
            mock_redis_client.delete.assert_called_once_with("user:1", "user:2")
