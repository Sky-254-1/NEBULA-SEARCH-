"""Notification repository."""
from datetime import datetime, timezone

from app.database.engine import DatabaseConnection


class NotificationRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        user_id: int,
        notif_type: str,
        category: str,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> int:
        await self._db.execute(
            "INSERT INTO notifications "
            "(user_id, type, category, title, message, data) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, notif_type, category, title, message, data or {}),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM notifications WHERE user_id = ? AND title = ? "
            "AND is_deleted = FALSE ORDER BY id DESC LIMIT 1",
            (user_id, title),
        )
        return row["id"] if row else 0

    async def list_for_user(self, user_id: int, limit: int = 50,
                            unread_only: bool = False) -> list[dict]:
        query = (
            "SELECT id, type, category, title, message, data, is_read, "
            "read_at, created_at, expires_at "
            "FROM notifications WHERE user_id = ? AND is_deleted = FALSE "
        )
        params: list = [user_id]
        if unread_only:
            query += "AND is_read = FALSE "
        query += "ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = await self._db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_unread_count(self, user_id: int) -> int:
        row = await self._db.fetchone(
            "SELECT COUNT(*) as cnt FROM notifications "
            "WHERE user_id = ? AND is_read = FALSE AND is_deleted = FALSE",
            (user_id,),
        )
        return row["cnt"] if row else 0

    async def mark_read(self, notif_id: int, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE notifications SET is_read = TRUE, read_at = ? "
            "WHERE id = ? AND user_id = ? AND is_deleted = FALSE",
            (now, notif_id, user_id),
        )
        await self._db.commit()

    async def mark_all_read(self, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE notifications SET is_read = TRUE, read_at = ? "
            "WHERE user_id = ? AND is_read = FALSE AND is_deleted = FALSE",
            (now, user_id),
        )
        await self._db.commit()

    async def delete(self, notif_id: int, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE notifications SET is_deleted = TRUE, deleted_at = ? "
            "WHERE id = ? AND user_id = ? AND is_deleted = FALSE",
            (now, notif_id, user_id),
        )
        await self._db.commit()
