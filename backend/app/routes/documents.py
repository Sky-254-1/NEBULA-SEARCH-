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

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}


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
    file: UploadFile = File(...),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload a new document for indexing."""
    # Validate file type before database lookup
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

    user_id = await _user_id(db, email)

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    upload_dir = settings.storage_uploads / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / safe_name
    dest.write_bytes(content)

    docs = DocumentRepository(db)
    doc_id = await docs.create(user_id, file.filename or safe_name, file.content_type, str(dest))

    await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})

    return DocumentResponse(
        id=doc_id,
        filename=file.filename or safe_name,
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