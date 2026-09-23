"""Citation tracking for retrieved chunks."""

from app.database.engine import DatabaseConnection


class CitationRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        user_id: int,
        query: str,
        document_id: int | None,
        chunk_id: int | None,
        snippet: str | None,
        score: float,
    ) -> int:
        await self._db.execute(
            "INSERT INTO citations (user_id, document_id, chunk_id, query, snippet, score) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, document_id, chunk_id, query, snippet, score),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM citations WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        return row["id"] if row else 0

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT id, document_id, chunk_id, query, snippet, score, created_at "
            "FROM citations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in rows]

    async def list_by_query(self, user_id: int, query: str, limit: int = 20) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT id, document_id, chunk_id, query, snippet, score, created_at "
            "FROM citations WHERE user_id = ? AND query = ? "
            "ORDER BY score DESC, created_at DESC LIMIT ?",
            (user_id, query, limit),
        )
        return [dict(row) for row in rows]
