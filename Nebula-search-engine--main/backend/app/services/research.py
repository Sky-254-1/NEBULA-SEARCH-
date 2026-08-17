"""
Research Hub service layer.
Handles business logic for projects, notes, bookmarks, citations, and AI research.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ResearchProject, ResearchNote, ResearchBookmark, ResearchCitation

logger = logging.getLogger(__name__)


class ResearchService:
    """Service for research hub operations."""

    # ============================================================================
    # Project Operations
    # ============================================================================

    async def create_project(
        self,
        db: AsyncSession,
        owner_id: UUID,
        title: str,
        description: Optional[str] = None,
        tags: list[str] = None,
    ) -> ResearchProject:
        """Create a new research project."""
        project = ResearchProject(
            owner_id=owner_id,
            title=title,
            description=description,
            tags=tags or [],
        )
        db.add(project)
        await db.flush()
        return project

    async def get_project(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
    ) -> Optional[ResearchProject]:
        """Get a research project by ID."""
        result = await db.execute(
            select(ResearchProject)
            .where(ResearchProject.id == project_id)
            .where(ResearchProject.owner_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_archived: bool = False,
    ) -> list[ResearchProject]:
        """List all research projects for a user."""
        query = (
            select(ResearchProject)
            .where(ResearchProject.owner_id == user_id)
            .order_by(ResearchProject.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        if not include_archived:
            query = query.where(ResearchProject.is_archived == False)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_project(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        **updates,
    ) -> Optional[ResearchProject]:
        """Update a research project."""
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return None
        
        for key, value in updates.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        
        project.updated_at = datetime.utcnow()
        await db.flush()
        return project

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a research project."""
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return False
        
        await db.delete(project)
        return True

    # ============================================================================
    # Note Operations
    # ============================================================================

    async def create_note(
        self,
        db: AsyncSession,
        project_id: UUID,
        author_id: UUID,
        title: str,
        content: str,
        source_url: Optional[str] = None,
        tags: list[str] = None,
    ) -> ResearchNote:
        """Create a research note."""
        note = ResearchNote(
            project_id=project_id,
            author_id=author_id,
            title=title,
            content=content,
            source_url=source_url,
            tags=tags or [],
        )
        db.add(note)
        await db.flush()
        return note

    async def get_note(
        self,
        db: AsyncSession,
        note_id: UUID,
        user_id: UUID,
    ) -> Optional[ResearchNote]:
        """Get a research note by ID."""
        result = await db.execute(
            select(ResearchNote)
            .join(ResearchProject)
            .where(ResearchNote.id == note_id)
            .where(ResearchProject.owner_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_notes(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        tags: Optional[list[str]] = None,
    ) -> list[ResearchNote]:
        """List notes in a project."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return []
        
        query = (
            select(ResearchNote)
            .where(ResearchNote.project_id == project_id)
            .order_by(ResearchNote.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        if tags:
            for tag in tags:
                query = query.where(ResearchNote.tags.contains([tag]))
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_note(
        self,
        db: AsyncSession,
        note_id: UUID,
        user_id: UUID,
        **updates,
    ) -> Optional[ResearchNote]:
        """Update a research note."""
        note = await self.get_note(db, note_id, user_id)
        if not note:
            return None
        
        for key, value in updates.items():
            if hasattr(note, key) and value is not None:
                setattr(note, key, value)
        
        note.updated_at = datetime.utcnow()
        await db.flush()
        return note

    async def delete_note(
        self,
        db: AsyncSession,
        note_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a research note."""
        note = await self.get_note(db, note_id, user_id)
        if not note:
            return False
        
        await db.delete(note)
        return True

    # ============================================================================
    # Bookmark Operations
    # ============================================================================

    async def create_bookmark(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        url: str,
        title: str,
        description: Optional[str] = None,
        tags: list[str] = None,
    ) -> ResearchBookmark:
        """Create a research bookmark."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            raise ValueError("Project not found")
        
        bookmark = ResearchBookmark(
            project_id=project_id,
            user_id=user_id,
            url=url,
            title=title,
            description=description,
            tags=tags or [],
        )
        db.add(bookmark)
        await db.flush()
        return bookmark

    async def list_bookmarks(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchBookmark]:
        """List bookmarks in a project."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return []
        
        result = await db.execute(
            select(ResearchBookmark)
            .where(ResearchBookmark.project_id == project_id)
            .order_by(ResearchBookmark.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_bookmark(
        self,
        db: AsyncSession,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a research bookmark."""
        result = await db.execute(
            select(ResearchBookmark)
            .join(ResearchProject)
            .where(ResearchBookmark.id == bookmark_id)
            .where(ResearchProject.owner_id == user_id)
        )
        bookmark = result.scalar_one_or_none()
        
        if not bookmark:
            return False
        
        await db.delete(bookmark)
        return True

    # ============================================================================
    # Citation Operations
    # ============================================================================

    async def create_citation(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        source_type: str,
        title: str,
        authors: list[str],
        note_id: Optional[UUID] = None,
        publication_date: Optional[datetime] = None,
        url: Optional[str] = None,
        quote: Optional[str] = None,
    ) -> ResearchCitation:
        """Create a citation."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            raise ValueError("Project not found")
        
        citation = ResearchCitation(
            project_id=project_id,
            note_id=note_id,
            source_type=source_type,
            title=title,
            authors=authors,
            publication_date=publication_date,
            url=url,
            quote=quote,
        )
        db.add(citation)
        await db.flush()
        return citation

    async def list_citations(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchCitation]:
        """List citations in a project."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return []
        
        result = await db.execute(
            select(ResearchCitation)
            .where(ResearchCitation.project_id == project_id)
            .order_by(ResearchCitation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ============================================================================
    # AI-Assisted Research
    # ============================================================================

    async def ai_research_query(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        query: str,
        context_note_ids: Optional[list[UUID]] = None,
    ) -> dict:
        """
        Perform AI-assisted research query.
        Analyzes project notes and generates a comprehensive summary.
        """
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            raise ValueError("Project not found")
        
        # Get notes
        if context_note_ids:
            notes_result = await db.execute(
                select(ResearchNote)
                .where(ResearchNote.id.in_(context_note_ids))
                .where(ResearchNote.project_id == project_id)
            )
            notes = notes_result.scalars().all()
        else:
            notes = await self.list_notes(db, project_id, user_id, limit=100)
        
        # Get citations
        citations = await self.list_citations(db, project_id, user_id, limit=100)
        
        # TODO: Implement actual AI analysis using OpenAI or similar
        # For now, return a basic summary
        
        note_summaries = [f"- {note.title}: {note.content[:200]}..." for note in notes[:10]]
        summary_text = f"# Research Summary\n\n## Query: {query}\n\n"
        summary_text += f"Analyzed {len(notes)} notes and {len(citations)} citations.\n\n"
        summary_text += "## Key Notes\n" + "\n".join(note_summaries) if note_summaries else "No notes found."
        
        return {
            "summary": summary_text,
            "key_findings": [
                "Finding 1: Placeholder for AI-generated finding",
                "Finding 2: Placeholder for AI-generated finding",
            ],
            "related_notes": notes[:10],
            "sources": citations[:10],
        }

    async def export_project(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        format: str = "markdown",
    ) -> str:
        """Export research project in various formats."""
        # Verify project ownership
        project = await self.get_project(db, project_id, user_id)
        if not project:
            raise ValueError("Project not found")
        
        notes = await self.list_notes(db, project_id, user_id, limit=1000)
        bookmarks = await self.list_bookmarks(db, project_id, user_id, limit=1000)
        citations = await self.list_citations(db, project_id, user_id, limit=1000)
        
        if format == "markdown":
            output = f"# {project.title}\n\n"
            if project.description:
                output += f"{project.description}\n\n"
            
            output += "## Notes\n\n"
            for note in notes:
                output += f"### {note.title}\n\n{note.content}\n\n"
            
            output += "## Bookmarks\n\n"
            for bookmark in bookmarks:
                output += f"- [{bookmark.title}]({bookmark.url})\n"
            
            output += "\n## Citations\n\n"
            for citation in citations:
                output += f"- {citation.title} by {', '.join(citation.authors)}\n"
            
            return output
        
        elif format == "json":
            import json
            return json.dumps({
                "project": {
                    "title": project.title,
                    "description": project.description,
                    "tags": project.tags,
                },
                "notes": [
                    {
                        "title": note.title,
                        "content": note.content,
                        "source_url": note.source_url,
                        "tags": note.tags,
                    }
                    for note in notes
                ],
                "bookmarks": [
                    {
                        "url": bookmark.url,
                        "title": bookmark.title,
                        "description": bookmark.description,
                    }
                    for bookmark in bookmarks
                ],
            }, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {format}")