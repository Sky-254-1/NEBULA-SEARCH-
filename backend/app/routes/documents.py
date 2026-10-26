"""Documents domain: upload, list, delete documents."""

import logging
import os
import re
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

logger = logging.getLogger("nebula.documents")

from app.config import get_settings
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import DocumentListResponse, DocumentResponse, PaginationMeta
from app.services.auth import get_current_user
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams
from app.middleware.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
settings = get_settings()

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}

# MIME type allowlist for content-type validation
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "application/pdf",
    "text/html",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# PDF file signature: %PDF-
PDF_HEADER = b"%PDF-"
# DOCX is a ZIP archive with specific structure
DOCX_SIGNATURE = b"PK\x03\x04"  # ZIP local file header (used by docx)
# JSON/HTML/CSV/TXT have no magic bytes, content-type is used as fallback


def _validate_extension(filename: str) -> tuple[bool, str]:
    """Validate file extension against allowlist."""
    if not filename:
        return False, "No filename provided"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed: {ext}"
    return True, ""


def _validate_content_type(content_type: str | None) -> bool:
    """Check if MIME type is in allowlist."""
    if not content_type:
        return False
    # Normalize MIME type (strip parameters like charset=utf-8)
    base_type = content_type.split(";")[0].strip().lower()
    return base_type in ALLOWED_MIME_TYPES


async def _validate_content(file: UploadFile, filename: str, content_type: str | None) -> None:
    """Validate file content safely using magic bytes."""
    file_bytes = await file.read(1024)  # Read only first 1KB for signature check
    await file.seek(0)  # Reset for subsequent reads

    if not file_bytes:
        return

    # Check PDF signature
    if filename.lower().endswith(".pdf"):
        if not file_bytes.startswith(PDF_HEADER):
            raise HTTPException(status_code=400, detail="Invalid PDF file signature")

    # Check DOCX signature (ZIP-based)
    if filename.lower().endswith(".docx"):
        if not file_bytes.startswith(DOCX_SIGNATURE):
            raise HTTPException(status_code=400, detail="Invalid DOCX file signature")


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    if not filename:
        return ""
    # Remove directory components and path separators
    filename = Path(filename).name
    # Remove control characters and non-ASCII characters
    filename = re.sub(r"[^\w\-. ]", "", filename, flags=re.UNICODE)
    # Strip leading/trailing whitespace and dots
    filename = filename.strip().strip(".")
    return filename or "unnamed"
async def _stream_and_save_file(
    file: UploadFile, dest: Path, max_bytes: int
) -> int:
    """
    Stream file content in chunks and save to disk.
    Returns total bytes written.
    Raises HTTPException if file exceeds max_bytes.
    """
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB chunks
    tmp_path = dest.with_suffix(dest.suffix + ".PartTemp")

    try:
        with open(tmp_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    # Clean up partial file
                    if tmp_path.exists():
                        tmp_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (max {max_bytes // (1024 * 1024)}MB)",
                    )
                f.write(chunk)

        # Atomic replace
        os.replace(tmp_path, dest)
        return total_bytes
    except HTTPException:
        # Re-raise HTTPException
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    except Exception:
        # Clean up on any other error
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    pagination: PaginationParams = Depends(),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all documents for the current user with pagination."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    
    # Get all documents (in production, add pagination to repository)
    rows = await docs.list_for_user(user_id)
    total = len(rows)
    
    # Apply pagination
    start_idx = pagination.offset
    end_idx = start_idx + pagination.limit
    paginated_rows = rows[start_idx:end_idx]
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size,
        has_previous=pagination.page > 1,
    )
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=r["id"],
                filename=r["filename"],
                content_type=r.get("content_type"),
                indexed_at=r.get("indexed_at"),
                created_at=str(r["created_at"]),
            )
            for r in paginated_rows
        ],
        pagination=pagination_meta,
    )


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    request,
    file: UploadFile = File(...),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload a new document for indexing."""
    # Rate limit: 10 uploads per minute per user
    await rate_limit(request, limit=10, window=60)

    # Validate file type before database lookup
    is_valid, error_msg = _validate_extension(file.filename or "")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Validate content type
    if not _validate_content_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Content-Type not allowed: {file.content_type}",
        )

    user_id = await _user_id(db, email)

    # Ensure storage directory exists before writing
    storage_dir = settings.storage_uploads / str(user_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Generate server-controlled storage name
    ext = Path(file.filename or "").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = storage_dir / safe_name

    # Stream and validate file content
    try:
        total_bytes = await _stream_and_save_file(file, dest, MAX_UPLOAD_BYTES)
        # Validate content signature
        await _validate_content(file, file.filename or safe_name, file.content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("File processing error: %s", e)
        raise HTTPException(status_code=400, detail="Invalid file content")

    # Create database record AFTER file is successfully written
    try:
        docs = DocumentRepository(db)
        doc_id = await docs.create(
            user_id,
            _sanitize_filename(file.filename or safe_name),
            file.content_type,
            str(dest),
        )

        # Enqueue indexing job
        await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})
    except Exception:
        # Cleanup file if DB insertion fails
        if dest.exists():
            try:
                dest.unlink()
            except Exception:
                pass
        raise

    return DocumentResponse(
        id=doc_id,
        filename=file.filename or safe_name,
        content_type=file.content_type,
        created_at="",
        status="pending",
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Delete a document and its indexed data."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    row = await docs.get_by_id(doc_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(row["storage_path"])
    if path.exists():
        path.unlink()
    await docs.delete(doc_id, user_id)
    return {"message": "Document deleted"}