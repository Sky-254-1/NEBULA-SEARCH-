from app.database.engine import DatabaseConnection

class BookmarkRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, user_id: int, title: str, url: str, snippet: str | None, tags: list[str] | None) -> int:
        row = await self.db.fetchone(
            "INSERT INTO bookmarks (user_id, title, url, snippet, tags) VALUES (?, ?, ?, ?, ?) RETURNING id",
            (user_id, title, url, snippet, ",".join(tags) if tags else None),
        )
        return row["id"] if row else None

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[dict]:
        rows = await self.db.fetchall(
            "SELECT * FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        for r in rows:
            if r.get("tags"):
                r["tags"] = r["tags"].split(",") if isinstance(r["tags"], str) else r["tags"]
            else:
                r["tags"] = []
        return rows

    async def get_by_id(self, bookmark_id: int, user_id: int) -> dict | None:
        r = await self.db.fetchone(
            "SELECT * FROM bookmarks WHERE id = ? AND user_id = ?",
            (bookmark_id, user_id),
        )
        if r and r.get("tags"):
            r["tags"] = r["tags"].split(",") if isinstance(r["tags"], str) else r["tags"]
        elif r:
            r["tags"] = []
        return r

    async def update(self, bookmark_id: int, user_id: int, **kwargs) -> None:
        sets = []
        params = []
        for key, val in kwargs.items():
            if val is not None:
                sets.append(f"{key} = ?")
                params.append(val if key != "tags" else ",".join(val) if val else None)
        if sets:
            params.extend([bookmark_id, user_id])
            await self.db.execute(
                 f"UPDATE bookmarks SET {', '.join(sets)} WHERE id = ? AND user_id = ?",  # nosec B608: SET columns come from kwargs keys, values are parameterized
                tuple(params),
            )
            await self.db.commit()

    async def delete(self, bookmark_id: int, user_id: int) -> None:
        await self.db.execute(
            "DELETE FROM bookmarks WHERE id = ? AND user_id = ?",
            (bookmark_id, user_id),
        )
        await self.db.commit()

    async def search(self, user_id: int, query: str) -> list[dict]:
        pattern = f"%{query}%"
        rows = await self.db.fetchall(
            "SELECT * FROM bookmarks WHERE user_id = ? AND (title LIKE ? OR url LIKE ? OR snippet LIKE ?) ORDER BY created_at DESC LIMIT 20",
            (user_id, pattern, pattern, pattern),
        )
        return rows
