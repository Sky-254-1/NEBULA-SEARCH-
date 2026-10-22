"""
Research Hub - Collaborative research and knowledge management.
Features: projects, notes, bookmarks, citations, and AI-assisted research.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database.engine import get_db
from app.services.research import ResearchService

router = APIRouter(prefix="/research", tags=["Research"])
research_service = ResearchService()


# ============================================================================
# Schemas
# ============================================================================


class ProjectCreate(BaseModel):
    """Create a new research project."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    """Update research project."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None


class ProjectResponse(BaseModel):
    """Research project response."""
    id: UUID
    title: str
    description: Optional[str]
    tags: list[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    owner_id: UUID
    note_count: int
    bookmark_count: int

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    """Create a research note."""
    project_id: UUID
    title: str = Field(..., max_length=255)
    content: str
    source_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Update research note."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[list[str]] = None


class NoteResponse(BaseModel):
    """Research note response."""
    id: UUID
    project_id: UUID
    title: str
    content: str
    source_url: Optional[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    author_id: UUID

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    """Create a research bookmark."""
    project_id: UUID
    url: str
    title: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class BookmarkResponse(BaseModel):
    """Research bookmark response."""
    id: UUID
    project_id: UUID
    url: str
    title: str
    description: Optional[str]
    tags: list[str]
    created_at: datetime
    user_id: UUID

    class Config:
        from_attributes = True


class CitationCreate(BaseModel):
    """Create a citation."""
    project_id: UUID
    note_id: Optional[UUID] = None
    source_type: str = Field(..., pattern="^(web|book|article|paper|other)$")
    title: str
    authors: list[str]
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    quote: Optional[str] = None


class CitationResponse(BaseModel):
    """Citation response."""
    id: UUID
    project_id: UUID
    note_id: Optional[UUID]
    source_type: str
    title: str
    authors: list[str]
    publication_date: Optional[datetime]
    url: Optional[str]
    quote: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchQuery(BaseModel):
    """AI-assisted research query."""
    project_id: UUID
    query: str
    context_notes: Optional[list[UUID]] = None


class ResearchSummary(BaseModel):
    """AI-generated research summary."""
    summary: str
    key_findings: list[str]
    related_notes: list[NoteResponse]
    sources: list[CitationResponse]


# ============================================================================
# Project Endpoints
# ============================================================================


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research project."""
    # Get current user from auth token
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    # Fetch user ID from database
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = await research_service.create_project(
        db=db,
        owner_id=user["id"],
        title=data.title,
        description=data.description,
        tags=data.tags,
    )
    await db.commit()
    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = False,
):
    """List all research projects for the current user."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    projects = await research_service.list_projects(
        db=db,
        user_id=user["id"],
        skip=skip,
        limit=limit,
        include_archived=include_archived,
    )
    return projects


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific research project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = await research_service.get_project(db, project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update a research project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = await research_service.update_project(
        db=db,
        project_id=project_id,
        user_id=user["id"],
        **data.dict(exclude_none=True),
    )
    await db.commit()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a research project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted = await research_service.delete_project(db, project_id, user["id"])
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


# ============================================================================
# Note Endpoints
# ============================================================================


@router.post("/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a research note."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    note = await research_service.create_note(
        db=db,
        project_id=data.project_id,
        author_id=user["id"],
        title=data.title,
        content=data.content,
        source_url=data.source_url,
        tags=data.tags,
    )
    await db.commit()
    return note


@router.get("/projects/{project_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tags: Optional[list[str]] = Query(None),
):
    """List notes in a project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    notes = await research_service.list_notes(
        db=db,
        project_id=project_id,
        user_id=user["id"],
        skip=skip,
        limit=limit,
        tags=tags,
    )
    return notes


@router.patch("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: UUID,
    data: NoteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update a research note."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    note = await research_service.update_note(
        db=db,
        note_id=note_id,
        user_id=user["id"],
        **data.dict(exclude_none=True),
    )
    await db.commit()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a research note."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted = await research_service.delete_note(db, note_id, user["id"])
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")


# ============================================================================
# Bookmark Endpoints
# ============================================================================


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    data: BookmarkCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a research bookmark."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bookmark = await research_service.create_bookmark(
        db=db,
        project_id=data.project_id,
        user_id=user["id"],
        url=data.url,
        title=data.title,
        description=data.description,
        tags=data.tags,
    )
    await db.commit()
    return bookmark


@router.get("/projects/{project_id}/bookmarks", response_model=list[BookmarkResponse])
async def list_bookmarks(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List bookmarks in a project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bookmarks = await research_service.list_bookmarks(
        db=db,
        project_id=project_id,
        user_id=user["id"],
        skip=skip,
        limit=limit,
    )
    return bookmarks


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a research bookmark."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted = await research_service.delete_bookmark(db, bookmark_id, user["id"])
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")


# ============================================================================
# Citation Endpoints
# ============================================================================


@router.post("/citations", response_model=CitationResponse, status_code=201)
async def create_citation(
    data: CitationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a citation."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    citation = await research_service.create_citation(
        db=db,
        project_id=data.project_id,
        note_id=data.note_id,
        source_type=data.source_type,
        title=data.title,
        authors=data.authors,
        publication_date=data.publication_date,
        url=data.url,
        quote=data.quote,
    )
    await db.commit()
    return citation


@router.get("/projects/{project_id}/citations", response_model=list[CitationResponse])
async def list_citations(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List citations in a project."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    citations = await research_service.list_citations(
        db=db,
        project_id=project_id,
        user_id=user["id"],
        skip=skip,
        limit=limit,
    )
    return citations


# ============================================================================
# AI-Assisted Research
# ============================================================================


@router.post("/query", response_model=ResearchSummary)
async def ai_research_query(
    query_data: ResearchQuery,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform AI-assisted research query.
    Analyzes project notes and generates a comprehensive summary.
    """
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = await research_service.ai_research_query(
        db=db,
        project_id=query_data.project_id,
        user_id=user["id"],
        query=query_data.query,
        context_note_ids=query_data.context_notes,
    )
    return summary


@router.get("/projects/{project_id}/export")
async def export_project(
    project_id: UUID,
    request: Request,
    format: str = Query("markdown", pattern="^(markdown|pdf|csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export research project in various formats."""
    from app.services.auth import get_current_user
    email = await get_current_user(request)
    
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    export_data = await research_service.export_project(
        db=db,
        project_id=project_id,
        user_id=user["id"],
        format=format,
    )
    
    media_types = {
        "markdown": "text/markdown",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "json": "application/json",
    }
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=export_data,
        media_type=media_types.get(format, "text/plain"),
        headers={
            "Content-Disposition": f"attachment; filename=research_project_{project_id}.{format}"
        },
    )