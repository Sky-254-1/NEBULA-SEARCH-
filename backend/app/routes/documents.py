"""Documents domain: upload, list, delete documents."""

import asyncio
import json
import mimetypes
import uuid
import zipfile
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
UPLOAD_READ_TIMEOUT_SECONDS = 60
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCX_ENTRIES = 1000
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


async def _store_upload_stream(file: UploadFile, destination: Path) -> int:
    """Write a bounded upload incrementally and validate the actual file bytes."""
    size = 0
    prefix = bytearray()
    try:
        with destination.open("xb") as output:
            async with asyncio.timeout(UPLOAD_READ_TIMEOUT_SECONDS):
                while chunk := await file.read(64 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
                    if len(prefix) < 1024:
                        prefix.extend(chunk[: 1024 - len(prefix)])
                    output.write(chunk)

        ext = destination.suffix.lower()
        if ext == ".pdf" and b"%PDF-" not in prefix:
            raise HTTPException(status_code=400, detail="Invalid PDF content")
        if ext == ".docx":
            if not prefix.startswith(b"PK\x03\x04"):
                raise HTTPException(status_code=400, detail="Invalid DOCX content")
            with zipfile.ZipFile(destination) as archive:
                members = archive.infolist()
                names = {member.filename for member in members}
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise HTTPException(status_code=400, detail="Invalid DOCX content")
                if len(members) > MAX_DOCX_ENTRIES:
                    raise HTTPException(status_code=400, detail="DOCX archive contains too many entries")
                total_uncompressed = 0
                for member in members:
                    member_path = Path(member.filename)
                    if member_path.is_absolute() or ".." in member.filename.replace("\\", "/").split("/"):
                        raise HTTPException(status_code=400, detail="Invalid DOCX archive path")
                    if (member.external_attr >> 16) & 0o170000 == 0o120000:
                        raise HTTPException(status_code=400, detail="Invalid DOCX archive entry")
                    total_uncompressed += member.file_size
                    if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                        raise HTTPException(status_code=400, detail="DOCX archive expands beyond the allowed size")
                    if member.file_size > max(member.compress_size, 1) * 100:
                        raise HTTPException(status_code=400, detail="DOCX archive compression ratio is unsafe")
        elif ext == ".json":
            with destination.open("r", encoding="utf-8-sig") as source:
                json.load(source)
        elif ext in {".txt", ".md", ".markdown", ".csv", ".html", ".htm"}:
            with destination.open("r", encoding="utf-8-sig") as source:
                for text_chunk in iter(lambda: source.read(8192), ""):
                    if "\x00" in text_chunk:
                        raise HTTPException(status_code=400, detail="Invalid text file content")
        return size
    except UnicodeDecodeError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="File must contain valid UTF-8 text") from exc
    except json.JSONDecodeError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid JSON file content") from exc
    except zipfile.BadZipFile as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid DOCX content") from exc
    except TimeoutError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=408, detail="Upload timed out") from exc
    except BaseException:
        destination.unlink(missing_ok=True)
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
    
    rows = await docs.list_for_user(
        user_id, limit=pagination.limit, offset=pagination.offset
    )
    total = await docs.count_for_user(user_id)
    
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
            for r in rows
        ],
        pagination=pagination_meta,
    )


@router.post("/", response_model=DocumentResponse, status_code=201)
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

    upload_dir = settings.storage_uploads / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / safe_name
    await _store_upload_stream(file, dest)

    docs = DocumentRepository(db)
    content_type = mimetypes.guess_type(file.filename or safe_name)[0] or "application/octet-stream"
    doc_id = await docs.create(user_id, file.filename or safe_name, content_type, str(dest))

    await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})

    return DocumentResponse(
        id=doc_id,
        filename=file.filename or safe_name,
        content_type=content_type,
        created_at="",
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int, email: str = Depends(get_current_user), db=Depends(get_db)
):
    """Get a single document by id (owner only)."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    row = await docs.get_by_id(doc_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=row["id"],
        filename=row["filename"],
        content_type=row.get("content_type"),
        indexed_at=row.get("indexed_at"),
        created_at=str(row["created_at"]),
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
