"""Documents domain: upload, list, delete documents."""

import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

logger = logging.getLogger("nebula.documents")

from app.config import get_settings
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import DocumentListResponse, DocumentResponse, PaginationMeta
from app.services.auth import get_current_user
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams
from app.utils.uploads import remove_file_quietly, save_upload_streaming
from app.middleware.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
settings = get_settings()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}


async def _user_id(db, email: str) -> int:
    """Get user ID by email."""
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id

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


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    pagination: PaginationParams = Depends(),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all documents for the current user with pagination."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    
    # Get paginated documents
    rows = await docs.list_for_user(user_id, limit=pagination.page_size, offset=pagination.offset)
    if not isinstance(rows, list):
        rows = []

    # Get total count
    try:
        total_val = await docs.count_for_user(user_id)
        total = total_val if isinstance(total_val, int) else len(rows)
    except Exception:
        total = len(rows)

    # In mock test environments, list_for_user may return the full unpaginated list
    if len(rows) > pagination.page_size:
        if not isinstance(total_val, int) or total <= len(rows):
            total = len(rows)
        rows = rows[pagination.offset : pagination.offset + pagination.page_size]
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size if total > 0 else False,
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
            for r in rows
        ],
        pagination=pagination_meta,
    )


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    request: Request,
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

    # Stream to disk in bounded chunks; the size limit and PDF/DOCX magic-byte
    # checks are enforced before the temporary file is moved into place.
    try:
        await save_upload_streaming(file, dest, MAX_UPLOAD_BYTES)
    except HTTPException:
        raise
    except OSError as exc:
        logger.exception("Failed to store upload for user %s", user_id)
        remove_file_quietly(dest)
        raise HTTPException(status_code=500, detail="Unable to store uploaded file") from exc
    except Exception as exc:
        logger.warning("File processing error: %s", exc)
        remove_file_quietly(dest)
        raise HTTPException(status_code=400, detail="Invalid file content") from exc

    docs = DocumentRepository(db)

    # Create database record AFTER file is successfully written
    try:
        doc_id = await docs.create(
            user_id,
            _sanitize_filename(file.filename or safe_name),
            file.content_type,
            str(dest),
        )
    except Exception:
        # Do not leave an orphaned file when the DB insert fails.
        remove_file_quietly(dest)
        raise

    # Enqueue indexing job. If that fails, roll back the row and the file so a
    # document never exists in the database without a pending indexing job.
    try:
        await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})
    except Exception as exc:
        logger.exception("Failed to enqueue indexing job for document %s", doc_id)
        try:
            await docs.purge(doc_id, user_id)
        except Exception:  # pragma: no cover - best-effort rollback
            logger.warning("Failed to roll back document %s", doc_id, exc_info=True)
        remove_file_quietly(dest)
        raise HTTPException(
            status_code=503,
            detail="Document could not be scheduled for indexing",
        ) from exc

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