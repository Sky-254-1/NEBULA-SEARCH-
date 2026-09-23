"""Search history repository for tracking user searches."""

from datetime import datetime

from app.database.engine import DatabaseConnection


class SearchHistoryRepository:
    """Repository for search history data access."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def record_search(
        self,
        user_id: int,
        query: str,
        result_count: int,
        search_type: str = "hybrid",
        response_time_ms: float = 0.0,
    ) -> int:
        """Record a search event."""
        await self._db.execute(
            """INSERT INTO search_history 
            (user_id, query, result_count, search_type, response_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                query,
                result_count,
                search_type,
                response_time_ms,
                datetime.now().isoformat(),
            ),
        )
        await self._db.commit()
        cursor = await self._db.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_user_history(
        self, user_id: int, limit: int = 50, days: int = 30
    ) -> list[dict]:
        """Get search history for a user."""
        rows = await self._db.fetchall(
            """SELECT * FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC 
            LIMIT ?""",
            (user_id, f"-{days} days", limit),
        )
        return [dict(row) for row in rows]

    async def get_popular_searches(
        self, limit: int = 10, days: int = 7
    ) -> list[dict]:
        """Get popular search queries."""
        rows = await self._db.fetchall(
            """SELECT query, COUNT(*) as search_count, 
            AVG(result_count) as avg_results,
            MAX(created_at) as last_searched
            FROM search_history 
            WHERE created_at >= datetime('now', ?)
            GROUP BY query 
            ORDER BY search_count DESC 
            LIMIT ?""",
            (f"-{days} days", limit),
        )
        return [dict(row) for row in rows]

    async def get_user_queries(self, user_id: int, days: int = 30) -> list[str]:
        """Get distinct queries for a user."""
        rows = await self._db.fetchall(
            """SELECT DISTINCT query FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC""",
            (user_id, f"-{days} days"),
        )
        return [row["query"] for row in rows]

    async def delete_history_item(self, user_id: int, search_id: int) -> bool:
        """Delete a search history item."""
        await self._db.execute(
            "DELETE FROM search_history WHERE id = ? AND user_id = ?",
            (search_id, user_id),
        )
        await self._db.commit()
        return True

    async def clear_user_history(self, user_id: int) -> None:
        """Clear all search history for a user."""
        await self._db.execute(
            "DELETE FROM search_history WHERE user_id = ?", (user_id,)
        )
        await self._db.commit()