"""Tests for streaming upload handling."""

import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.utils.uploads import save_upload_streaming


def make_upload(content: bytes, filename: str = "doc.txt") -> UploadFile:
    return UploadFile(
        io.BytesIO(content),
        size=len(content),
        filename=filename,
        headers=Headers({"content-type": "text/plain"}),
    )


@pytest.mark.asyncio
async def test_streaming_upload_writes_file(tmp_path):
    dest = tmp_path / "out.txt"

    written = await save_upload_streaming(make_upload(b"hello world"), dest, 1024)

    assert written == 11
    assert dest.read_bytes() == b"hello world"
    assert list(tmp_path.glob("*.part")) == []


@pytest.mark.asyncio
async def test_oversized_upload_is_rejected_and_cleaned_up(tmp_path):
    dest = tmp_path / "out.txt"

    with pytest.raises(HTTPException) as exc_info:
        await save_upload_streaming(make_upload(b"x" * 200), dest, 100)

    assert exc_info.value.status_code == 413
    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []


@pytest.mark.asyncio
async def test_oversized_multichunk_upload_is_rejected(tmp_path):
    """The limit applies while streaming, before the whole file is buffered."""
    dest = tmp_path / "big.txt"

    with pytest.raises(HTTPException) as exc_info:
        await save_upload_streaming(make_upload(b"x" * (200 * 1024)), dest, 64 * 1024)

    assert exc_info.value.status_code == 413
    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []


@pytest.mark.asyncio
async def test_invalid_pdf_signature_is_rejected_and_cleaned_up(tmp_path):
    dest = tmp_path / "out.pdf"

    with pytest.raises(HTTPException) as exc_info:
        await save_upload_streaming(make_upload(b"not a pdf", "doc.pdf"), dest, 1024)

    assert exc_info.value.status_code == 400
    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []


@pytest.mark.asyncio
async def test_valid_pdf_signature_is_accepted(tmp_path):
    dest = tmp_path / "out.pdf"

    written = await save_upload_streaming(
        make_upload(b"%PDF-1.7\nbody", "doc.pdf"), dest, 1024
    )

    assert written > 0
    assert dest.read_bytes().startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_read_failure_leaves_no_partial_file(tmp_path):
    class BrokenUpload(UploadFile):
        async def read(self, size: int = -1) -> bytes:  # type: ignore[override]
            raise OSError("simulated read failure")

    dest = tmp_path / "out.txt"
    upload = BrokenUpload(io.BytesIO(b""), filename="doc.txt")

    with pytest.raises(OSError):
        await save_upload_streaming(upload, dest, 1024)

    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []
