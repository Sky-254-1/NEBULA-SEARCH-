"""Research Hub service using the application's shared database connection."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.config import get_settings
from app.database.engine import DatabaseConnection

_JSON_FIELDS = {"tags", "authors"}
_settings = get_settings()


def _db_id(value: UUID) -> UUID | str:
    return value if _settings.uses_postgres else str(value)


def _decode_row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for field in _JSON_FIELDS.intersection(result):
        value = result[field]
        if isinstance(value, str):
            result[field] = json.loads(value)
    return result


def _decode_rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [decoded for row in rows if (decoded := _decode_row(row)) is not None]


def _encode_json(value: Any) -> str:
    return json.dumps(value)


class ResearchService:
    """Business logic for projects, notes, bookmarks, citations, and research."""

    async def create_project(
        self,
        db: DatabaseConnection,
        owner_id: int,
        title: str,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        project_id = uuid4()
        row = await db.fetchone(
            """INSERT INTO research_projects
               (id, owner_id, title, description, tags)
               VALUES (?, ?, ?, ?, ?) RETURNING *""",
            (_db_id(project_id), owner_id, title, description, _encode_json(tags or [])),
        )
        project = _decode_row(row)
        if project is None:
            raise RuntimeError("Research project insert returned no row")
        project["note_count"] = 0
        project["bookmark_count"] = 0
        return project

    async def get_project(
        self, db: DatabaseConnection, project_id: UUID, user_id: int
    ) -> dict[str, Any] | None:
        row = await db.fetchone(
            """SELECT p.*,
                      (SELECT COUNT(*) FROM research_notes n WHERE n.project_id = p.id) AS note_count,
                      (SELECT COUNT(*) FROM research_bookmarks b WHERE b.project_id = p.id) AS bookmark_count
               FROM research_projects p
               WHERE p.id = ? AND p.owner_id = ?""",
            (_db_id(project_id), user_id),
        )
        return _decode_row(row)

    async def list_projects(
        self,
        db: DatabaseConnection,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        query = (
            """SELECT p.*,
                      (SELECT COUNT(*) FROM research_notes n WHERE n.project_id = p.id) AS note_count,
                      (SELECT COUNT(*) FROM research_bookmarks b WHERE b.project_id = p.id) AS bookmark_count
               FROM research_projects p
               WHERE p.owner_id = ?
               ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"""
            if include_archived
            else """SELECT p.*,
                           (SELECT COUNT(*) FROM research_notes n WHERE n.project_id = p.id) AS note_count,
                           (SELECT COUNT(*) FROM research_bookmarks b WHERE b.project_id = p.id) AS bookmark_count
                    FROM research_projects p
                    WHERE p.owner_id = ? AND p.is_archived = FALSE
                    ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"""
        )
        rows = await db.fetchall(query, (user_id, limit, skip))
        return _decode_rows(rows)

    async def update_project(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        **updates: Any,
    ) -> dict[str, Any] | None:
        fields = {"title", "description", "tags", "is_archived"}
        changes = {key: value for key, value in updates.items() if key in fields and value is not None}
        if changes:
            if "tags" in changes:
                changes["tags"] = _encode_json(changes["tags"])
            queries = {
                "title": "UPDATE research_projects SET title = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
                "description": "UPDATE research_projects SET description = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
                "tags": "UPDATE research_projects SET tags = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
                "is_archived": "UPDATE research_projects SET is_archived = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
            }
            for field, query in queries.items():
                if field in changes:
                    await db.execute(
                        query,
                        (changes[field], datetime.utcnow(), _db_id(project_id), user_id),
                    )
        return await self.get_project(db, project_id, user_id)

    async def delete_project(
        self, db: DatabaseConnection, project_id: UUID, user_id: int
    ) -> bool:
        if await self.get_project(db, project_id, user_id) is None:
            return False
        project_key = _db_id(project_id)
        await db.execute("DELETE FROM research_citations WHERE project_id = ?", (project_key,))
        await db.execute("DELETE FROM research_bookmarks WHERE project_id = ?", (project_key,))
        await db.execute("DELETE FROM research_notes WHERE project_id = ?", (project_key,))
        await db.execute(
            "DELETE FROM research_projects WHERE id = ? AND owner_id = ?",
            (project_key, user_id),
        )
        return True

    async def create_note(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        author_id: int,
        title: str,
        content: str,
        source_url: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if await self.get_project(db, project_id, author_id) is None:
            raise ValueError("Project not found")
        note_id = uuid4()
        row = await db.fetchone(
            """INSERT INTO research_notes
               (id, project_id, author_id, title, content, source_url, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *""",
            (
                _db_id(note_id),
                _db_id(project_id),
                author_id,
                title,
                content,
                source_url,
                _encode_json(tags or []),
            ),
        )
        note = _decode_row(row)
        if note is None:
            raise RuntimeError("Research note insert returned no row")
        return note

    async def get_note(
        self, db: DatabaseConnection, note_id: UUID, user_id: int
    ) -> dict[str, Any] | None:
        row = await db.fetchone(
            """SELECT n.* FROM research_notes n
               JOIN research_projects p ON p.id = n.project_id
               WHERE n.id = ? AND p.owner_id = ?""",
            (_db_id(note_id), user_id),
        )
        return _decode_row(row)

    async def list_notes(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        project = await self.get_project(db, project_id, user_id)
        if project is None:
            return []
        if not tags:
            rows = await db.fetchall(
                """SELECT * FROM research_notes WHERE project_id = ?
                   ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                (_db_id(project_id), limit, skip),
            )
            return _decode_rows(rows)

        rows = await db.fetchall(
            """SELECT * FROM research_notes WHERE project_id = ?
               ORDER BY updated_at DESC""",
            (_db_id(project_id),),
        )
        notes = _decode_rows(rows)
        selected_tags = set(tags)
        notes = [
            note for note in notes
            if selected_tags.issubset(set(note.get("tags", [])))
        ]
        return notes[skip : skip + limit]

    async def update_note(
        self, db: DatabaseConnection, note_id: UUID, user_id: int, **updates: Any
    ) -> dict[str, Any] | None:
        note = await self.get_note(db, note_id, user_id)
        if note is None:
            return None
        fields = {"title", "content", "source_url", "tags"}
        changes = {key: value for key, value in updates.items() if key in fields and value is not None}
        if changes:
            if "tags" in changes:
                changes["tags"] = _encode_json(changes["tags"])
            queries = {
                "title": "UPDATE research_notes SET title = ?, updated_at = ? WHERE id = ?",
                "content": "UPDATE research_notes SET content = ?, updated_at = ? WHERE id = ?",
                "source_url": "UPDATE research_notes SET source_url = ?, updated_at = ? WHERE id = ?",
                "tags": "UPDATE research_notes SET tags = ?, updated_at = ? WHERE id = ?",
            }
            for field, query in queries.items():
                if field in changes:
                    await db.execute(
                        query,
                        (changes[field], datetime.utcnow(), _db_id(note_id)),
                    )
        return await self.get_note(db, note_id, user_id)

    async def delete_note(
        self, db: DatabaseConnection, note_id: UUID, user_id: int
    ) -> bool:
        note = await self.get_note(db, note_id, user_id)
        if note is None:
            return False
        await db.execute(
            "UPDATE research_citations SET note_id = NULL WHERE note_id = ?",
            (_db_id(note_id),),
        )
        await db.execute("DELETE FROM research_notes WHERE id = ?", (_db_id(note_id),))
        return True

    async def create_bookmark(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        url: str,
        title: str,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if await self.get_project(db, project_id, user_id) is None:
            raise ValueError("Project not found")
        bookmark_id = uuid4()
        row = await db.fetchone(
            """INSERT INTO research_bookmarks
               (id, project_id, user_id, url, title, description, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *""",
            (
                _db_id(bookmark_id),
                _db_id(project_id),
                user_id,
                url,
                title,
                description,
                _encode_json(tags or []),
            ),
        )
        bookmark = _decode_row(row)
        if bookmark is None:
            raise RuntimeError("Research bookmark insert returned no row")
        return bookmark

    async def list_bookmarks(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if await self.get_project(db, project_id, user_id) is None:
            return []
        rows = await db.fetchall(
            """SELECT * FROM research_bookmarks WHERE project_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (_db_id(project_id), limit, skip),
        )
        return _decode_rows(rows)

    async def delete_bookmark(
        self, db: DatabaseConnection, bookmark_id: UUID, user_id: int
    ) -> bool:
        row = await db.fetchone(
            """SELECT b.id FROM research_bookmarks b
               JOIN research_projects p ON p.id = b.project_id
               WHERE b.id = ? AND p.owner_id = ?""",
            (_db_id(bookmark_id), user_id),
        )
        if row is None:
            return False
        await db.execute("DELETE FROM research_bookmarks WHERE id = ?", (_db_id(bookmark_id),))
        return True

    async def create_citation(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        source_type: str,
        title: str,
        authors: list[str],
        note_id: UUID | None = None,
        publication_date: datetime | None = None,
        url: str | None = None,
        quote: str | None = None,
    ) -> dict[str, Any]:
        if await self.get_project(db, project_id, user_id) is None:
            raise ValueError("Project not found")
        if note_id is not None:
            note = await self.get_note(db, note_id, user_id)
            if note is None or str(note["project_id"]) != str(project_id):
                raise ValueError("Note not found in project")
        citation_id = uuid4()
        row = await db.fetchone(
            """INSERT INTO research_citations
               (id, project_id, note_id, source_type, title, authors,
                publication_date, url, quote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *""",
            (
                _db_id(citation_id),
                _db_id(project_id),
                _db_id(note_id) if note_id else None,
                source_type,
                title,
                _encode_json(authors),
                publication_date,
                url,
                quote,
            ),
        )
        citation = _decode_row(row)
        if citation is None:
            raise RuntimeError("Research citation insert returned no row")
        return citation

    async def list_citations(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if await self.get_project(db, project_id, user_id) is None:
            return []
        rows = await db.fetchall(
            """SELECT * FROM research_citations WHERE project_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (_db_id(project_id), limit, skip),
        )
        return _decode_rows(rows)

    async def ai_research_query(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        query: str,
        context_note_ids: list[UUID] | None = None,
    ) -> dict[str, Any]:
        if await self.get_project(db, project_id, user_id) is None:
            raise ValueError("Project not found")
        if context_note_ids:
            notes = []
            for note_id in context_note_ids:
                note = await self.get_note(db, note_id, user_id)
                if note is not None and str(note["project_id"]) == str(_db_id(project_id)):
                    notes.append(note)
            notes.sort(
                key=lambda note: str(note.get("updated_at", "")),
                reverse=True,
            )
        else:
            notes = await self.list_notes(db, project_id, user_id, limit=100)
        citations = await self.list_citations(db, project_id, user_id, limit=100)
        note_summaries = [
            f"- {note['title']}: {note['content'][:200]}..." for note in notes[:10]
        ]
        summary = f"# Research Summary\n\n## Query: {query}\n\n"
        summary += f"Analyzed {len(notes)} notes and {len(citations)} citations.\n\n"
        summary += (
            "## Key Notes\n" + "\n".join(note_summaries)
            if note_summaries
            else "No notes found."
        )
        return {
            "summary": summary,
            "key_findings": [
                "Finding 1: Placeholder for AI-generated finding",
                "Finding 2: Placeholder for AI-generated finding",
            ],
            "related_notes": notes[:10],
            "sources": citations[:10],
        }

    async def export_project(
        self,
        db: DatabaseConnection,
        project_id: UUID,
        user_id: int,
        format: str = "markdown",
    ) -> str:
        project = await self.get_project(db, project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        notes = await self.list_notes(db, project_id, user_id, limit=1000)
        bookmarks = await self.list_bookmarks(db, project_id, user_id, limit=1000)
        citations = await self.list_citations(db, project_id, user_id, limit=1000)

        if format == "markdown":
            output = f"# {project['title']}\n\n"
            if project.get("description"):
                output += f"{project['description']}\n\n"
            output += "## Notes\n\n"
            for note in notes:
                output += f"### {note['title']}\n\n{note['content']}\n\n"
            output += "## Bookmarks\n\n"
            for bookmark in bookmarks:
                output += f"- [{bookmark['title']}]({bookmark['url']})\n"
            output += "\n## Citations\n\n"
            for citation in citations:
                output += f"- {citation['title']} by {', '.join(citation['authors'])}\n"
            return output
        if format == "json":
            return json.dumps(
                {
                    "project": {
                        "title": project["title"],
                        "description": project["description"],
                        "tags": project["tags"],
                    },
                    "notes": [
                        {
                            "title": note["title"],
                            "content": note["content"],
                            "source_url": note["source_url"],
                            "tags": note["tags"],
                        }
                        for note in notes
                    ],
                    "bookmarks": [
                        {
                            "url": bookmark["url"],
                            "title": bookmark["title"],
                            "description": bookmark["description"],
                        }
                        for bookmark in bookmarks
                    ],
                },
                indent=2,
            )
        raise ValueError(f"Unsupported format: {format}")
