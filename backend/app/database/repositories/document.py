"""Document repository."""

from datetime import datetime, timezone

from app.database.engine import DatabaseConnection


class DocumentRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        storage_path: str,
    ) -> int:
        await self._db.execute(
            "INSERT INTO documents (user_id, filename, content_type, storage_path) VALUES (?, ?, ?, ?)",
            (user_id, filename, content_type, storage_path),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM documents WHERE user_id = ? AND storage_path = ? ORDER BY id DESC LIMIT 1",
            (user_id, storage_path),
        )
        return row["id"] if row else 0

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT id, filename, content_type, storage_path, indexed_at, created_at, "
            "status, content_hash, error_message "
            "FROM documents WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in rows]

    async def get_by_id(self, doc_id: int, user_id: int):
        return await self._db.fetchone(
            "SELECT id, filename, content_type, storage_path, indexed_at, created_at, "
            "status, content_hash, error_message "
            "FROM documents WHERE id = ? AND user_id = ?",
            (doc_id, user_id),
        )

    async def delete(self, doc_id: int, user_id: int) -> bool:
        row = await self.get_by_id(doc_id, user_id)
        if not row:
            return False
        await self._db.execute("DELETE FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
        await self._db.commit()
        return True

    async def mark_indexed(self, doc_id: int, content_hash: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if content_hash:
            await self._db.execute(
                "UPDATE documents SET indexed_at = ?, status = ?, content_hash = ?, error_message = NULL WHERE id = ?",
                (now, "indexed", content_hash, doc_id),
            )
        else:
            await self._db.execute(
                "UPDATE documents SET indexed_at = ?, status = ?, error_message = NULL WHERE id = ?",
                (now, "indexed", doc_id),
            )
        await self._db.commit()

    async def set_status(
        self,
        doc_id: int,
        status: str,
        content_hash: str | None = None,
        error_message: str | None = None,
    ) -> None:
        await self._db.execute(
            "UPDATE documents SET status = ?, content_hash = ?, error_message = ? WHERE id = ?",
            (status, content_hash, error_message, doc_id),
        )
        await self._db.commit()

    async def find_by_hash(self, user_id: int, content_hash: str) -> dict | None:
        row = await self._db.fetchone(
            "SELECT id, filename, content_hash, status FROM documents "
            "WHERE user_id = ? AND content_hash = ? AND status = 'indexed'",
            (user_id, content_hash),
        )
        return dict(row) if row else None

    async def count_all(self) -> int:
        """Return total document count across all users."""
        row = await self._db.fetchone("SELECT COUNT(*) as count FROM documents")
        return int(row["count"]) if row else 0
