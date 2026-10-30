"""Upload size, content-validation, and cleanup regressions."""

import asyncio
import io
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException
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


@pytest.mark.asyncio
async def test_docx_expansion_is_bounded(client: AsyncClient, auth_headers: dict, monkeypatch):
    monkeypatch.setattr(documents, "MAX_DOCX_UNCOMPRESSED_BYTES", 100)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "types")
        archive.writestr("word/document.xml", "x" * 200)

    response = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("large.docx", payload.getvalue(), "application/zip")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_timeout_removes_partial_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_READ_TIMEOUT_SECONDS", 0.01)
    destination = tmp_path / "partial.txt"

    class SlowUpload:
        async def read(self, _size: int) -> bytes:
            await asyncio.sleep(0.05)
            return b"late"

    with pytest.raises(HTTPException) as error:
        await documents._store_upload_stream(SlowUpload(), destination)
    assert error.value.status_code == 408
    assert not destination.exists()


@pytest.mark.asyncio
async def test_interrupted_upload_removes_partial_file(tmp_path: Path):
    destination = tmp_path / "partial.txt"

    class InterruptedUpload:
        def __init__(self):
            self.reads = 0

        async def read(self, _size: int) -> bytes:
            self.reads += 1
            if self.reads == 1:
                return b"partial"
            raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await documents._store_upload_stream(InterruptedUpload(), destination)
    assert not destination.exists()


@pytest.mark.asyncio
async def test_malicious_filename_uses_generated_storage_name(
    client: AsyncClient, auth_headers: dict, monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(documents, "settings", type("Settings", (), {"storage_uploads": tmp_path})())
    response = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("../../outside.txt", b"safe content", "text/plain")},
    )
    assert response.status_code == 201
    stored = list(tmp_path.rglob("*.txt"))
    assert len(stored) == 1
    assert stored[0].parent.parent == tmp_path
    assert stored[0].name != "outside.txt"
