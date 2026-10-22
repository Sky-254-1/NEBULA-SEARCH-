"""Middleware unit tests."""

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.rate_limit import rate_limit
from app.middleware.security import SecurityHeadersMiddleware


@pytest.mark.asyncio
async def test_rate_limit_allows_requests():
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "client": ("127.0.0.1", 1234)}
    request = Request(scope)
    await rate_limit(request)


@pytest.mark.asyncio
async def test_security_headers_middleware():
    middleware = SecurityHeadersMiddleware(app=None)

    async def call_next(req):
        return Response("ok")

    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    request = Request(scope)
    response = await middleware.dispatch(request, call_next)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
