"""Chat history repository."""

from app.database.engine import DatabaseConnection


class ChatRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def add_message(self, user_id: int, role: str, content: str) -> None:
        await self._db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await self._db.commit()

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT role, content, created_at FROM chat_history "
            "WHERE user_id = ? ORDER BY created_at ASC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in rows]

    async def clear_for_user(self, user_id: int) -> None:
        await self._db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        await self._db.commit()
