"""Enhanced rate limiter with Redis backing, sliding window, and standard headers."""

import logging
import asyncio
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.services.cache import cache_service

settings = get_settings()
logger = logging.getLogger("nebula.ratelimit")

_REDIS_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + (tonumber(clock[2]) / 1000000)
local cutoff = now - window
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
redis.call('ZADD', key, now, member)
local count = redis.call('ZCARD', key)
redis.call('EXPIRE', key, window + 1)
if count > limit then
  redis.call('ZREM', key, member)
  count = count - 1
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry_after = window
  if oldest[2] then
    retry_after = math.max(1, math.ceil(tonumber(oldest[2]) + window - now))
  end
  return {0, count, retry_after, now + window}
end
return {1, count, 0, now + window}
"""


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    limit: int  # Max requests
    window: int = 60  # Time window in seconds
    burst_limit: Optional[int] = None  # Max burst requests
    burst_window: int = 10  # Burst window in seconds


class RateLimiter:
    """Enhanced rate limiter with sliding window and multiple limit types."""
    
    def __init__(self):
        self._memory_store: dict[str, list[tuple[float, str]]] = defaultdict(list)
        self._memory_lock = asyncio.Lock()
        self._max_memory_keys = 10000
    
    async def check_rate_limit(
        self,
        request: Request,
        config: RateLimitConfig,
        identifier: str,
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.
        Returns (is_allowed, rate_limit_info).
        """
        now = time.time()
        
        # Check burst limit first (if configured)
        if config.burst_limit:
            burst_key = f"ratelimit:burst:{identifier}:{request.url.path}"
            burst_allowed, burst_info = await self._check_sliding_window(
                burst_key,
                config.burst_limit,
                config.burst_window,
                now,
            )
            if not burst_allowed:
                return False, {
                    "limit": config.burst_limit,
                    "remaining": 0,
                    "reset": burst_info["reset"],
                    "retry_after": burst_info["retry_after"],
                }
        
        # Check main rate limit
        rate_key = f"ratelimit:{identifier}:{request.url.path}"
        allowed, info = await self._check_sliding_window(
            rate_key,
            config.limit,
            config.window,
            now,
        )
        
        if not allowed:
            return False, {
                "limit": config.limit,
                "remaining": 0,
                "reset": info["reset"],
                "retry_after": info["retry_after"],
            }
        
        return True, {
            "limit": config.limit,
            "remaining": info["remaining"],
            "reset": info["reset"],
            "retry_after": 0,
        }
    
    async def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window: int,
        now: float,
    ) -> tuple[bool, dict]:
        """Check sliding window rate limit."""
        if limit <= 0:
            return False, {"reset": now + max(window, 1), "retry_after": max(window, 1)}

        # Try Redis first
        if cache_service._redis:
            try:
                redis_key = f"sliding:{key}"
                request_id = uuid.uuid4().hex
                allowed, count, retry_after, reset = await cache_service._redis.eval(
                    _REDIS_SLIDING_WINDOW_SCRIPT,
                    1,
                    redis_key,
                    window,
                    limit,
                    request_id,
                )
                if not allowed:
                    return False, {"reset": reset, "retry_after": retry_after}
                return True, {
                    "remaining": limit - count,
                    "reset": reset,
                }
            except Exception as exc:
                logger.debug("Redis rate limit fallback: %s", exc)
        
        # Fallback to in-memory sliding window
        window_key = f"mem:{key}"
        async with self._memory_lock:
            entries = [
                (timestamp, member)
                for timestamp, member in self._memory_store.get(window_key, [])
                if timestamp > now - window
            ]
            if entries:
                self._memory_store[window_key] = entries
            else:
                self._memory_store.pop(window_key, None)

            count = len(entries)
            if count >= limit:
                oldest = entries[0][0]
                retry_after = max(1, int(oldest + window - now) + 1)
                return False, {"reset": now + window, "retry_after": retry_after}

            if window_key not in self._memory_store and len(self._memory_store) >= self._max_memory_keys:
                oldest_key = min(
                    self._memory_store,
                    key=lambda k: self._memory_store[k][-1][0],
                )
                self._memory_store.pop(oldest_key, None)

            entries.append((now, uuid.uuid4().hex))
            self._memory_store[window_key] = entries
            return True, {"remaining": limit - count - 1, "reset": now + window}


# Global rate limiter instance
rate_limiter = RateLimiter()


# ---------------------------------------------------------------------------
# SlowAPI compatibility wrappers
# ---------------------------------------------------------------------------


def get_limiter():
    """
    Compatibility wrapper for SlowAPI's get_limiter().
    Returns the global rate limiter instance.
    """
    return rate_limiter


async def rate_limit_exceeded_handler(request: Request, exc: HTTPException):
    """
    Compatibility wrapper for SlowAPI's rate limit exceeded handler.
    Returns a proper JSON response with rate limit headers.
    """
    headers = exc.headers or {}
    retry_after = headers.get("Retry-After", "60")
    return JSONResponse(
        status_code=429,
        content={"detail": exc.detail},
        headers={
            "X-RateLimit-Limit": headers.get("X-RateLimit-Limit", str(settings.rate_limit_per_minute)),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": headers.get("X-RateLimit-Reset", str(int(time.time() + 60))),
            "Retry-After": retry_after,
        },
    )


# Note: slowapi_middleware is not needed as we use our custom middleware
# This is kept as None for backward compatibility in imports
slowapi_middleware = None


async def rate_limit(
    request: Request,
    limit: Optional[int] = None,
    window: int = 60,
    burst_limit: Optional[int] = None,
    burst_window: int = 10,
) -> None:
    """
    Enhanced rate limiting with sliding window and standard headers.
    
    Args:
        request: FastAPI request
        limit: Max requests per window (uses default if None)
        window: Time window in seconds
        burst_limit: Max burst requests
        burst_window: Burst time window in seconds
    """
    limit = limit or settings.rate_limit_per_minute
    config = RateLimitConfig(
        limit=limit,
        window=window,
        burst_limit=burst_limit,
        burst_window=burst_window,
    )
    
    # Determine identifier (IP, user, or API key)
    identifier = await _get_rate_limit_identifier(request)
    
    # Check rate limit
    allowed, info = await rate_limiter.check_rate_limit(request, config, identifier)
    
    # Add rate limit headers to response
    request.state.rate_limit_info = info
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again shortly.",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(info["reset"])),
                "Retry-After": str(info["retry_after"]),
            },
        )


async def _get_rate_limit_identifier(request: Request) -> str:
    """Get identifier for rate limiting (user, API key, or IP)."""
    # Try to get authenticated user
    try:
        from app.services.auth import get_current_user_token_payload
        payload = await get_current_user_token_payload(request)
        user_id = payload.get("sub", "")
        if user_id:
            return f"user:{user_id}"
    except Exception as exc:
        logger.debug("Rate limit auth extraction failed, falling back to API key/IP: %s", exc)
    
    # Try API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"  # Use first 16 chars for privacy
    
    # Fallback to IP
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


def rate_limit_auth(limit: int, window: int = 60):
    """Create rate limiter for auth endpoints."""
    async def limiter(request: Request):
        await rate_limit(request, limit=limit, window=window)
    return limiter


# Pre-configured rate limiters for common use cases
limit_signup = rate_limit_auth(settings.signup_rate_limit, 3600)  # Per hour
limit_login = rate_limit_auth(settings.login_rate_limit, 900)  # Per 15 minutes
limit_refresh = rate_limit_auth(settings.refresh_rate_limit, 900)  # Per 15 minutes


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """Add rate limit headers to all responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Add rate limit info if available
        if hasattr(request.state, "rate_limit_info"):
            info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", settings.rate_limit_per_minute))
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(int(info.get("reset", time.time() + 60)))
        
        return response
