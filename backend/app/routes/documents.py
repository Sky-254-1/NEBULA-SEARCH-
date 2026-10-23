"""Documents domain: upload, list, delete documents."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import get_settings
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import DocumentListResponse, DocumentResponse, PaginationMeta
from app.services.auth import get_current_user
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
settings = get_settings()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Allowed extensions AND their expected MIME-type prefixes.
# We check *both* the client-supplied extension and the actual file magic bytes.
_ALLOWED: dict[str, tuple[str, ...]] = {
    ".txt":  ("text/",),
    ".md":   ("text/",),
    ".json": ("application/json", "text/"),
    ".csv":  ("text/", "application/"),
    ".pdf":  ("application/pdf",),
    ".html": ("text/html", "text/"),
    ".htm":  ("text/html", "text/"),
    ".docx": (
        "application/vnd.openxmlformats",
        "application/zip",   # DOCX is a ZIP archive internally
        "application/octet-stream",
    ),
}

# Magic-byte signatures (first N bytes) that we recognise.
# We use a lightweight internal check so we don't need the `python-magic` C lib.
_MAGIC: list[tuple[bytes, str]] = [
    (b"%PDF",            "application/pdf"),
    (b"PK\x03\x04",     "application/zip"),       # ZIP / DOCX / XLSX …
    (b"\xd0\xcf\x11\xe0", "application/msoffice"), # Legacy OLE (.doc, .xls)
    (b"<!DOCTYPE",       "text/html"),
    (b"<html",           "text/html"),
    (b"<HTML",           "text/html"),
    (b"{",               "application/json"),
    (b"[",               "application/json"),
]


def _sniff_mime(header: bytes) -> str:
    """Return a best-guess MIME type from the first 16 bytes of file content.

    Falls back to ``"text/plain"`` for anything that looks like plain text,
    or ``"application/octet-stream"`` for unrecognised binary data.
    """
    for sig, mime in _MAGIC:
        if header[: len(sig)].lower().startswith(sig.lower()):
            return mime
    # Heuristic: if all sampled bytes are printable ASCII / UTF-8 control chars
    # treat as plain text.
    try:
        header.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        return "application/octet-stream"


def _validate_upload(filename: str, content: bytes) -> None:
    """Raise HTTPException if the upload fails extension or MIME checks."""
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: '{ext}'. "
            f"Permitted extensions: {', '.join(sorted(_ALLOWED))}",
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed")

    # MIME sniff against the first 16 bytes
    sniffed = _sniff_mime(content[:16])
    allowed_prefixes = _ALLOWED[ext]
    if not any(sniffed.startswith(p) for p in allowed_prefixes):
        raise HTTPException(
            status_code=400,
            detail=(
                f"File content does not match its extension '{ext}' "
                f"(detected content type: {sniffed!r}). "
                "Please upload a genuine file of the declared type."
            ),
        )


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    pagination: PaginationParams = Depends(),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all documents for the current user with pagination."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)

    rows = await docs.list_for_user(user_id)
    total = len(rows)

    start_idx = pagination.offset
    end_idx = start_idx + pagination.limit
    paginated_rows = rows[start_idx:end_idx]

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
    file: UploadFile = File(...),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload a new document for indexing.

    Validates both file extension *and* actual file content (magic bytes)
    before accepting the upload. Filenames are sanitised server-side; the
    original name is stored for display purposes only.
    """
    original_filename = file.filename or "upload"

    # Read first then validate — avoids double-read and ensures size check is accurate
    content = await file.read()
    _validate_upload(original_filename, content)

    user_id = await _user_id(db, email)

    ext = Path(original_filename).suffix.lower()

    # Server-generated filename — never trust user-supplied paths
    upload_dir = settings.storage_uploads / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / safe_name
    dest.write_bytes(content)

    docs = DocumentRepository(db)
    doc_id = await docs.create(user_id, original_filename, file.content_type, str(dest))

    await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})

    return DocumentResponse(
        id=doc_id,
        filename=original_filename,
        content_type=file.content_type,
        created_at="",
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
