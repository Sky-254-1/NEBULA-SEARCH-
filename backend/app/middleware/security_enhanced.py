"""Enhanced security middleware for 100% safety target."""

import re
import time
from typing import Dict, Any
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Hardened security headers (also present in security.py; duplicated here so
# that middleware/security_enhanced.py alone is sufficient when only the
# enhanced stack is mounted).
# ---------------------------------------------------------------------------


class HardenedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attaches a comprehensive, CSP-aware security header set.

    Guarantees these headers are present on every response:
    * Content-Security-Policy       — driven from Settings.csp_policy
    * X-Content-Type-Options        — nosniff
    * X-Frame-Options               — DENY
    * Referrer-Policy               — strict-origin-when-cross-origin
    * Strict-Transport-Security     — max-age + includeSubDomains + preload (prod only)

    Additional OWASP-recommended headers:
    * X-XSS-Protection
    * Permissions-Policy
    * Cross-Origin-Embedder-Policy / Opener-Policy / Resource-Policy
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = settings.permissions_policy

        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        response.headers["Content-Security-Policy"] = settings.csp_policy
        response.headers["Cross-Origin-Embedder-Policy"] = settings.cross_origin_embedder_policy
        response.headers["Cross-Origin-Opener-Policy"] = settings.cross_origin_opener_policy
        response.headers["Cross-Origin-Resource-Policy"] = settings.cross_origin_resource_policy

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate all incoming requests for malicious input."""

    _MAX_JSON_DEPTH = 10
    _MAX_STRING_LENGTH = 10000
    _MAX_ARRAY_LENGTH = 1000
    _MAX_OBJECT_KEYS = 100

    _SQL_INJECTION_PATTERNS = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|TRUNCATE)\b)"
        r"|(';)|(--)|(\/\*)|(\*\/)|(\bOR\b\s+\d+\s*=\s*\d+)",
        re.IGNORECASE,
    )

    _XSS_PATTERNS = re.compile(
        r"<script[^>]*>|</script>|javascript:|on\w+\s*=",
        re.IGNORECASE,
    )

    # Paths where SQL-keyword checks are intentionally skipped (user search input)
    _SEARCH_PATHS = re.compile(
        r"^/api/v\d+/(search|query|suggest|autocomplete|spell|trending|popular)",
        re.IGNORECASE,
    )

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            self._validate_headers(request)
            if request.method in ("POST", "PUT", "PATCH"):
                await self._validate_body(request, request.url.path)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"detail": str(exc)})
        return await call_next(request)

    def _validate_headers(self, request: Request) -> None:
        """Validate request headers."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            raise ValueError("Request too large")

        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 1024:
            raise ValueError("Invalid User-Agent header")

    async def _validate_body(self, request: Request, path: str = "") -> None:
        """Validate request body for injection attacks."""
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return

        # Skip SQL injection check for search/query endpoints — users legitimately
        # search for "how to SELECT rows" or "DROP TABLE tutorial" etc.
        is_search_endpoint = bool(self._SEARCH_PATHS.match(path))

        try:
            body = await request.json()
            self._validate_value(body, depth=0, skip_sql_check=is_search_endpoint)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid JSON: {exc}")

    def _validate_value(self, value: Any, depth: int, skip_sql_check: bool = False) -> None:
        """Recursively validate JSON values."""
        if depth > self._MAX_JSON_DEPTH:
            raise ValueError("JSON depth exceeded")

        if isinstance(value, str):
            if len(value) > self._MAX_STRING_LENGTH:
                raise ValueError("String too long")
            if not skip_sql_check and self._SQL_INJECTION_PATTERNS.search(value):
                raise ValueError("Potential SQL injection detected")
            if self._XSS_PATTERNS.search(value):
                raise ValueError("Potential XSS detected")

        elif isinstance(value, dict):
            if len(value) > self._MAX_OBJECT_KEYS:
                raise ValueError("Too many object keys")
            for k, v in value.items():
                if not isinstance(k, str) or len(k) > 100:
                    raise ValueError("Invalid object key")
                self._validate_value(v, depth + 1, skip_sql_check=skip_sql_check)

        elif isinstance(value, list):
            if len(value) > self._MAX_ARRAY_LENGTH:
                raise ValueError("Array too long")
            for item in value:
                self._validate_value(item, depth + 1, skip_sql_check=skip_sql_check)


import logging as _logging

_rl_logger = _logging.getLogger("nebula.ratelimit")


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting with per-user/IP limits.

    NOTE: This implementation is per-process in-memory. Behind multiple
    workers each worker maintains its own window, effectively multiplying
    the limit by the worker count. For consistent limits in production
    deploy with a single worker or use the Redis-backed RateLimitHeadersMiddleware.
    """

    def __init__(self, app):
        super().__init__(app)
        self._requests: Dict[str, list[float]] = defaultdict(list)
        self._user_requests: Dict[str, list[float]] = defaultdict(list)
        if settings.redis_url:
            _rl_logger.warning(
                "AdvancedRateLimitMiddleware: Redis is configured but rate limit counters "
                "are still in-memory per-process. Set WORKERS=1 or migrate to Redis-backed "
                "rate limiting for accurate per-user/IP limits across workers."
            )

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if not self._check_rate_limit(f"ip:{client_ip}", now, settings.rate_limit_per_minute):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            if not self._check_rate_limit(f"user:{user_id}", now, settings.rate_limit_per_minute * 2):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "User rate limit exceeded"},
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)

    def _check_rate_limit(self, key: str, now: float, limit: int) -> bool:
        """Check if request is within rate limit."""
        window_start = now - 60.0
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(now)
        return True


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Audit logging for security events."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.enable_audit_logs:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", "unknown")
        user = getattr(request.state, "user", None)
        user_id = str(user.id) if user else None

        response = await call_next(request)

        if response.status_code >= 400:
            try:
                from app.database.engine import connect
                from app.database.repositories.audit import AuditRepository

                db = await connect()
                try:
                    repo = AuditRepository(db)
                    await repo.log(
                        user_id=user_id,
                        action=f"{request.method} {request.url.path}",
                        status="failed" if response.status_code >= 500 else "denied",
                        ip=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        metadata={"status_code": response.status_code, "request_id": request_id},
                    )
                finally:
                    await db.close()
            except Exception:
                pass

        return response