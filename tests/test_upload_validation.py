"""Upload size and content-validation regressions."""

import pytest
from httpx import AsyncClient

from app.routes import documents


@pytest.mark.asyncio
async def test_upload_limit_is_enforced_while_streaming(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    monkeypatch.setattr(documents, "MAX_UPLOAD_BYTES", 5)
    response = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("oversized.txt", b"123456789", "text/plain")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_rejects_non_utf8_text_disguised_as_txt(
    client: AsyncClient, auth_headers: dict
):
    response = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("malicious.txt", b"\xff\x00\xfe", "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_invalid_pdf_content(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
