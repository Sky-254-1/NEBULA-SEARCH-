"""Security headers and CSRF protection middleware."""

import hashlib
import hmac
import secrets
from typing import Literal, Optional, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response."""

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


# ---------------------------------------------------------------------------
# CSRF: double-submit cookie pattern
# ---------------------------------------------------------------------------

_CSRF_COOKIE_NAME = "csrf_token"
_CSRF_HEADER_NAME = "x-csrf-token"
_CSRF_TOKEN_BYTES = 32
_CSRF_COOKIE_MAX_AGE = 3600  # 1 hour


def _generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(_CSRF_TOKEN_BYTES)


def _constant_time_equal(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


_SameSiteT = Literal["lax", "strict", "none"]

def _set_csrf_cookie(response: Response, token: str) -> None:
    """Attach the CSRF cookie to a response using configured security flags."""
    samesite = cast(_SameSiteT, settings.cookie_samesite)
    response.set_cookie(
        key=_CSRF_COOKIE_NAME,
        value=token,
        max_age=_CSRF_COOKIE_MAX_AGE,
        path="/",
        secure=settings.cookie_secure,
        httponly=False,  # MUST be readable by JS so it can be echoed in the header
        samesite=samesite,
    )


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection using the **double-submit cookie** pattern.

    How it works
    ------------
    1. On any safe (read-only) request the middleware plants a ``csrf_token``
       cookie if one is not already set.  The cookie is **not** HttpOnly so
       client-side JavaScript can read its value.
    2. On state-changing methods (POST / PUT / DELETE / PATCH) the caller must
       mirror the cookie value in the ``X-CSRF-Token`` header.  The middleware
       verifies the two values match using a constant-time comparison.
    3. Pure API clients authenticating with ``Authorization: Bearer …`` are
       exempt — CSRF is a browser/cookie vector.

    This pattern is stateless: no tokens are stored server-side.

    Additionally, session-bound tokens can be generated and validated
    programmatically via :meth:`generate_csrf_token`, :meth:`get_csrf_token`,
    and :meth:`_validate_csrf_token` using an in-memory token store with TTL.

    References
    ----------
    * https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie
    """

    EXEMPT_PREFIXES = (
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
        "/favicon.ico",
        "/static/",
    )

    STATE_CHANGING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    _TOKEN_TTL = 3600

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._session_tokens: dict[str, tuple[str, float]] = {}

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate and store a CSRF token bound to ``session_id``.

        Returns the generated token string (>= 32 URL-safe characters).
        """
        import time as _time
        token = _generate_csrf_token()
        self._session_tokens[session_id] = (token, _time.time())
        return token

    def get_csrf_token(self, session_id: str) -> Optional[str]:
        """Return the active token for ``session_id`` or ``None`` if missing/expired."""
        import time as _time
        entry = self._session_tokens.get(session_id)
        if entry is None:
            return None
        token, ts = entry
        if (_time.time() - ts) > self._TOKEN_TTL:
            del self._session_tokens[session_id]
            return None
        return token

    def _validate_csrf_token(self, token: str) -> bool:
        """Return ``True`` iff ``token`` belongs to an active non-expired session."""
        import time as _time
        if not token or not isinstance(token, str):
            return False
        now = _time.time()
        expired_sessions: list[str] = []
        found = False
        for sid, (stored_token, ts) in self._session_tokens.items():
            if (now - ts) > self._TOKEN_TTL:
                expired_sessions.append(sid)
                continue
            if _constant_time_equal(stored_token, token):
                found = True
        for sid in expired_sessions:
            del self._session_tokens[sid]
        return found

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        # Fast-path 1: safe methods -> ensure cookie is planted, no further check
        if method not in self.STATE_CHANGING_METHODS:
            response = await call_next(request)
            existing = request.cookies.get(_CSRF_COOKIE_NAME)
            if not existing:
                _set_csrf_cookie(response, _generate_csrf_token())
            return response

        # Fast-path 2: exempt paths (docs / probes / static assets)
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Fast-path 3: pure API-token auth is not susceptible to CSRF
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # Fast-path 4: no auth header AND no cookie -> not a browser session;
        # defer to the auth layer which will return 401, rather than a 403.
        has_cookie_auth = bool(request.cookies)
        if not auth_header and not has_cookie_auth:
            return await call_next(request)

        # --- Perform double-submit check ---
        cookie_token = request.cookies.get(_CSRF_COOKIE_NAME, "")
        header_token = request.headers.get(_CSRF_HEADER_NAME, "")

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing (cookie + header required)"},
            )

        if not _constant_time_equal(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Request size limiter
# ---------------------------------------------------------------------------


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request size to prevent DoS attacks."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return Response(
                status_code=413,
                content={"detail": "Request too large"},
                media_type="application/json",
            )
        if hasattr(request, "content_length") and request.content_length:
            if request.content_length > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request too large"},
                )
        return await call_next(request)


# ---------------------------------------------------------------------------
# IP whitelist (for admin-only sub-sets of routes)
# ---------------------------------------------------------------------------


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Optional IP whitelist — blocks requests from non-allowed IPs."""

    def __init__(self, app, allowed_ips: Optional[list[str]] = None):
        super().__init__(app)
        self.allowed_ips = allowed_ips or []

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.allowed_ips:
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied from this IP"},
            )
        return await call_next(request)


csrf_protection = CSRFProtectionMiddleware