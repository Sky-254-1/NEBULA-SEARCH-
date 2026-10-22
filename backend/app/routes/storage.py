"""Storage routes: documents, settings, exports."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import get_settings
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.export import ExportRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import (
    DocumentListResponse,
    DocumentResponse,
    ExportCreateRequest,
    ExportListResponse,
    ExportResponse,
    PaginationMeta,
    SettingsResponse,
    SettingsUpdateRequest,
)
from app.services.auth import get_current_user
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/v1/storage", tags=["Storage"])
settings = get_settings()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    rows = await docs.list_for_user(user_id)
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
        ]
    )


@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

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


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
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


@router.get("/settings", response_model=SettingsResponse)
async def get_settings_route(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _user_id(db, email)
    repo = SettingsRepository(db)
    return SettingsResponse(settings=await repo.get_for_user(user_id))


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdateRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    repo = SettingsRepository(db)
    merged = await repo.upsert(user_id, body.settings)
    return SettingsResponse(settings=merged)


@router.post("/exports", response_model=ExportResponse)
async def create_export(
    body: ExportCreateRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    export_dir = settings.storage_exports / str(user_id)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{body.export_type}_{uuid.uuid4().hex}.json"
    dest = export_dir / filename

    payload = {"type": body.export_type, "user_id": user_id, "data": body.data or {}}
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exports = ExportRepository(db)
    export_id = await exports.create(user_id, body.export_type, str(dest))
    now = datetime.now(timezone.utc).isoformat()
    return ExportResponse(id=export_id, export_type=body.export_type, storage_path=str(dest), created_at=now)


@router.get("/exports", response_model=ExportListResponse)
async def list_exports(
    pagination: PaginationParams = Depends(),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all exports for the current user with pagination."""
    user_id = await _user_id(db, email)
    exports = ExportRepository(db)
    
    # Get all exports (in production, add pagination to repository)
    rows = await exports.list_for_user(user_id)
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
    
    return ExportListResponse(
        exports=[
            ExportResponse(
                id=r["id"],
                export_type=r["export_type"],
                storage_path=r["storage_path"],
                created_at=str(r["created_at"]),
            )
            for r in paginated_rows
        ],
        pagination=pagination_meta,
    )
