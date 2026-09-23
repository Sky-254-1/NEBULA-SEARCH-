"""Export job repository."""

from app.database.engine import DatabaseConnection


class ExportRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(self, user_id: int, export_type: str, storage_path: str) -> int:
        await self._db.execute(
            "INSERT INTO exports (user_id, export_type, storage_path) VALUES (?, ?, ?)",
            (user_id, export_type, storage_path),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM exports WHERE user_id = ? AND storage_path = ? ORDER BY id DESC LIMIT 1",
            (user_id, storage_path),
        )
        return row["id"] if row else 0

    async def list_for_user(self, user_id: int, limit: int = 20) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT id, export_type, storage_path, created_at FROM exports "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in rows]
