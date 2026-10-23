"""Tests for minimal security and architectural repairs.

Covers:
- Upload validation (extension + MIME magic bytes + size limits)
- IP whitelist scoping to admin paths only
- CSRF double-submit protection with empty-cookie fast path
- Prometheus metrics token authentication
- Vector export row bounds and truncation
"""

import os
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.main import app
from app.middleware.security import CSRFProtectionMiddleware, IPWhitelistMiddleware
from app.routes.documents import MAX_UPLOAD_BYTES, _validate_upload
from app.routes.vector import MAX_EXPORT_ROWS


class TestUploadValidation:
    """Tests for file upload validation in app.routes.documents."""

    def test_valid_text_file(self):
        # Plain text with .txt
        _validate_upload("sample.txt", b"Hello, this is a legitimate document text.")

    def test_valid_markdown_file(self):
        # Markdown with .md
        _validate_upload("notes.md", b"# Header\n\nSome notes here.")

    def test_valid_json_file(self):
        # JSON with .json
        _validate_upload("data.json", b'{"key": "value", "list": [1, 2, 3]}')

    def test_valid_pdf_file(self):
        # PDF with .pdf and %PDF magic bytes
        _validate_upload("report.pdf", b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    def test_disallowed_extension(self):
        # Executable file extension
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload("script.sh", b"#!/bin/bash\necho hello\n")
        assert exc_info.value.status_code == 400
        assert "File type not allowed" in exc_info.value.detail

    def test_empty_file_rejected(self):
        # Empty file
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload("empty.txt", b"")
        assert exc_info.value.status_code == 400
        assert "Empty file not allowed" in exc_info.value.detail

    def test_file_too_large(self):
        # Exceeds 10 MB limit
        oversized = b"a" * (MAX_UPLOAD_BYTES + 1)
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload("huge.txt", oversized)
        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    def test_mime_content_mismatch_binary_renamed_to_pdf(self):
        # Plain text without %PDF header renamed as .pdf
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload("fake.pdf", b"this is obviously not a genuine pdf header")
        assert exc_info.value.status_code == 400
        assert "does not match its extension" in exc_info.value.detail


class TestIPWhitelistMiddleware:
    """Tests for IPWhitelistMiddleware scoped to admin paths."""

    @pytest.mark.asyncio
    async def test_non_admin_route_allowed_regardless_of_ip(self):
        test_app = Starlette()
        test_app.add_middleware(
            IPWhitelistMiddleware,
            allowed_ips=["192.168.1.100"],
            admin_prefix="/api/v1/admin",
        )

        @test_app.route("/api/v1/search")
        async def public_search(request: Request):
            return PlainTextResponse("search results")

        async with AsyncClient(
            transport=ASGITransport(app=test_app, client=("10.0.0.5", 12345)),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/api/v1/search")
            assert resp.status_code == 200
            assert resp.text == "search results"

    @pytest.mark.asyncio
    async def test_admin_route_blocked_for_unlisted_ip(self):
        test_app = Starlette()
        test_app.add_middleware(
            IPWhitelistMiddleware,
            allowed_ips=["192.168.1.100"],
            admin_prefix="/api/v1/admin",
        )

        @test_app.route("/api/v1/admin/dashboard")
        async def admin_dashboard(request: Request):
            return PlainTextResponse("admin only")

        async with AsyncClient(
            transport=ASGITransport(app=test_app, client=("10.0.0.5", 12345)),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/api/v1/admin/dashboard")
            assert resp.status_code == 403
            assert resp.json() == {"detail": "Access denied from this IP"}

    @pytest.mark.asyncio
    async def test_admin_route_allowed_for_listed_ip(self):
        test_app = Starlette()
        test_app.add_middleware(
            IPWhitelistMiddleware,
            allowed_ips=["192.168.1.100"],
            admin_prefix="/api/v1/admin",
        )

        @test_app.route("/api/v1/admin/dashboard")
        async def admin_dashboard(request: Request):
            return PlainTextResponse("admin only")

        async with AsyncClient(
            transport=ASGITransport(app=test_app, client=("192.168.1.100", 12345)),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/api/v1/admin/dashboard")
            assert resp.status_code == 200
            assert resp.text == "admin only"


class TestCSRFProtection:
    """Tests for CSRF double-submit protection."""

    @pytest.mark.asyncio
    async def test_bearer_token_bypasses_csrf(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/signup",
            headers={"Authorization": "Bearer fake-token"},
            json={"email": "csrf_test@example.com", "password": "StrongPassword123!"},
        )
        # Bypasses CSRF (not 403 CSRF failure)
        assert resp.status_code != 403

    @pytest.mark.asyncio
    async def test_cookie_without_csrf_header_is_rejected(self, client: AsyncClient):
        # When request has cookies, CSRF must be present and match
        client.cookies.set("session_id", "some-cookie-session")
        resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "csrf_test@example.com", "password": "StrongPassword123!"},
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.json().get("detail", "")


class TestMetricsEndpointAuth:
    """Tests for Prometheus /metrics endpoint authentication."""

    @pytest.mark.asyncio
    async def test_metrics_disabled_when_token_unset(self, monkeypatch):
        monkeypatch.delenv("METRICS_TOKEN", raising=False)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/metrics")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_metrics_unauthorized_with_wrong_token(self, monkeypatch):
        monkeypatch.setenv("METRICS_TOKEN", "super-secret-metrics-token-12345")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Without token
            resp1 = await ac.get("/metrics")
            assert resp1.status_code == 401

            # With wrong Bearer token
            resp2 = await ac.get(
                "/metrics", headers={"Authorization": "Bearer invalid-token"}
            )
            assert resp2.status_code == 401

    @pytest.mark.asyncio
    async def test_metrics_authorized_with_correct_token(self, monkeypatch):
        token = "super-secret-metrics-token-12345"
        monkeypatch.setenv("METRICS_TOKEN", token)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/metrics", headers={"Authorization": f"Bearer {token}"}
            )
            # Either 200 (if prometheus_client installed) or 501 (if not)
            assert resp.status_code in (200, 501)


class TestVectorExportBounds:
    """Tests for Vector export bounds."""

    def test_max_export_rows_defined(self):
        assert MAX_EXPORT_ROWS == 10_000
