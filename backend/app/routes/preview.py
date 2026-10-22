"""Document preview routes for mobile WebView."""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.services.auth import get_current_user

settings = get_settings()
router = APIRouter(prefix="/api/v1/documents/preview", tags=["Document Preview"])


class PreviewRequest(BaseModel):
    document_id: int
    page: Optional[int] = 1
    max_size_mb: Optional[int] = None


@router.get("/{document_id}")
async def get_document_preview(document_id: int, page: int = 1, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get document preview for mobile WebView."""
    if not settings.enable_document_preview:
        raise HTTPException(status_code=404, detail="Document preview is not enabled")
    
    docs = DocumentRepository(db)
    document = await docs.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check file size limit
    max_size = settings.max_preview_size_mb * 1024 * 1024
    file_path = Path(settings.storage_uploads) / document["filename"]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")
    
    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"Document too large for preview. Max size: {settings.max_preview_size_mb}MB"
        )
    
    # Generate preview based on file type
    content_type = document.get("content_type", "")
    
    if content_type.startswith("image/"):
        # Return image directly
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type=content_type)
    
    elif content_type == "application/pdf":
        # For PDFs, return the file (mobile can render it)
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type="application/pdf")
    
    elif content_type.startswith("text/") or content_type in ["application/json", "application/javascript"]:
        # Return text content
        content = file_path.read_text(encoding="utf-8")
        return {"content": content, "content_type": content_type}
    
    else:
        # For unsupported types, return metadata only
        return {
            "filename": document["filename"],
            "content_type": content_type,
            "size": file_size,
            "preview_available": False,
            "message": "Preview not available for this file type"
        }


@router.get("/{document_id}/metadata")
async def get_document_metadata(document_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get document metadata for preview."""
    docs = DocumentRepository(db)
    document = await docs.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document["id"],
        "filename": document["filename"],
        "content_type": document["content_type"],
        "size": document.get("size"),
        "created_at": document["created_at"],
        "indexed_at": document.get("indexed_at"),
    }