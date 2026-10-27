"""Shared streaming helpers for document uploads.

Uploads are written to a temporary file in the destination directory in
fixed-size chunks, so memory usage stays bounded regardless of the request
size. The temporary file is only moved into place after the size limit and
any signature checks have passed, and it is always removed on failure.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import HTTPException, UploadFile

logger = logging.getLogger("nebula.uploads")

CHUNK_SIZE = 64 * 1024  # 64 KiB

# Magic bytes for formats that can be checked cheaply.
PDF_HEADER = b"%PDF-"
DOCX_SIGNATURE = b"PK\x03\x04"  # ZIP local file header (DOCX is a ZIP archive)


def remove_file_quietly(path: Path) -> None:
    """Delete ``path`` if it exists, ignoring filesystem errors."""
    try:
        path.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - best-effort cleanup
        logger.debug("Could not remove %s", path, exc_info=True)


def validate_signature(path: Path, filename: str) -> None:
    """Reject PDF/DOCX uploads whose magic bytes do not match the extension."""
    try:
        with path.open("rb") as fh:
            header = fh.read(1024)
    except OSError as exc:  # pragma: no cover - the file was just written
        raise HTTPException(status_code=400, detail="Unable to read uploaded file") from exc

    if not header:
        return

    lower = (filename or "").lower()
    if lower.endswith(".pdf") and not header.startswith(PDF_HEADER):
        raise HTTPException(status_code=400, detail="Invalid PDF file signature")
    if lower.endswith(".docx") and not header.startswith(DOCX_SIGNATURE):
        raise HTTPException(status_code=400, detail="Invalid DOCX file signature")


async def save_upload_streaming(
    file: UploadFile,
    dest: Path,
    max_bytes: int,
    check_signature: bool = True,
) -> int:
    """Stream ``file`` to ``dest`` without buffering it in memory.

    The file is written to ``<dest>.part`` first. The limit is enforced while
    streaming, signatures are validated on the temporary file, and only then
    is the temporary file atomically renamed to ``dest``.

    Returns:
        Number of bytes written.

    Raises:
        HTTPException: ``413`` when the upload exceeds ``max_bytes``, or
            ``400`` when the magic-byte check fails.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_name(dest.name + ".part")
    remove_file_quietly(tmp_path)  # drop a stale partial from a previous crash

    total_bytes = 0
    try:
        with tmp_path.open("wb") as fh:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (max {max_bytes // (1024 * 1024)}MB)",
                    )
                fh.write(chunk)
            fh.flush()
            os.fsync(fh.fileno())

        if check_signature:
            validate_signature(tmp_path, file.filename or dest.name)

        os.replace(tmp_path, dest)
        return total_bytes
    except BaseException:
        # Also covers client disconnects (CancelledError) and validation errors.
        remove_file_quietly(tmp_path)
        raise
