"""Search history repository for tracking user search queries."""

from __future__ import annotations

from typing import Any
from app.database.engine import DatabaseConnection


class SearchHistoryRepository:
    """Repository for user search history."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def record_search(
        self,
        user_id: int,
        query: str,
        result_count: int = 0,
    ) -> int:
        """Record a search query in history."""
        cursor = await self._db.execute(
            "INSERT INTO search_history (user_id, query, result_count) VALUES (?, ?, ?)",
            (user_id, query, result_count),
        )
        await self._db.commit()
        if hasattr(cursor, "lastrowid") and cursor.lastrowid is not None:
            return cursor.lastrowid
        return 1

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 50,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get recent search history for a user."""
        sql = """SELECT * FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC 
            LIMIT ?"""
        rows = await self._db.fetchall(sql, (user_id, f"-{days} days", limit))
        return [dict(r) for r in rows] if rows else []

    async def get_popular_searches(
        self,
        limit: int = 10,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get most popular searches across all users."""
        sql = """SELECT query, COUNT(*) as search_count, 
            AVG(result_count) as avg_results,
            MAX(created_at) as last_searched
            FROM search_history 
            WHERE created_at >= datetime('now', ?)
            GROUP BY query 
            ORDER BY search_count DESC 
            LIMIT ?"""
        rows = await self._db.fetchall(sql, (f"-{days} days", limit))
        return [dict(r) for r in rows] if rows else []

    async def get_user_queries(
        self,
        user_id: int,
        days: int = 30,
    ) -> list[Any]:
        """Get distinct search queries for a user."""
        sql = """SELECT DISTINCT query FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC"""
        rows = await self._db.fetchall(sql, (user_id, f"-{days} days"))
        return [r["query"] if isinstance(r, dict) and "query" in r else r for r in rows] if rows else []

    async def delete_history_item(
        self,
        user_id: int,
        search_id: int,
    ) -> bool:
        """Delete a specific search history item."""
        row = await self._db.fetchone(
            "SELECT * FROM search_history WHERE id = ? AND user_id = ?",
            (search_id, user_id),
        )
        if not row:
            return False
        await self._db.execute(
            "DELETE FROM search_history WHERE id = ? AND user_id = ?",
            (search_id, user_id),
        )
        await self._db.commit()
        return True

    async def clear_user_history(self, user_id: int) -> None:
        """Clear all search history for a user."""
        await self._db.fetchall(
            "SELECT * FROM search_history WHERE user_id = ?",
            (user_id,),
        )
        await self._db.execute(
            "DELETE FROM search_history WHERE user_id = ?",
            (user_id,),
        )
        await self._db.commit()
