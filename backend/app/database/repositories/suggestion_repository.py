"""Search suggestions repository for trending, semantic, and related searches."""

from datetime import datetime
from typing import Any

from app.database.engine import DatabaseConnection


class SuggestionRepository:
    """Repository for search suggestions data operations."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    # ------------------------------------------------------------------ #
    # Trending queries
    # ------------------------------------------------------------------ #

    async def increment_trending_query(self, query: str) -> None:
        """Increment or create trending query entry."""
        await self._db.execute(
            """
            INSERT INTO trending_queries (query, frequency, searches_today,
                                         searches_week, searches_month,
                                         last_used, popularity_score)
            VALUES (?, 1, 1, 1, 1, ?, 1.0)
            ON CONFLICT(query) DO UPDATE SET
                frequency = frequency + 1,
                searches_today = searches_today + 1,
                searches_week = searches_week + 1,
                searches_month = searches_month + 1,
                last_used = excluded.last_used
            """,
            (query, datetime.now().isoformat()),
        )
        await self._db.commit()

    async def get_trending_queries(
        self, limit: int = 20, min_score: float = 0.0
    ) -> list[dict[str, Any]]:
        """Get trending queries ranked by popularity score."""
        rows = await self._db.fetchall(
            """
            SELECT query, frequency, searches_today, searches_week,
                   searches_month, growth_rate, popularity_score, last_used
            FROM trending_queries
            WHERE popularity_score >= ?
            ORDER BY popularity_score DESC, last_used DESC
            LIMIT ?
            """,
            (min_score, limit),
        )
        return [dict(row) for row in rows]

    async def update_trending_metrics(self) -> int:
        """Recalculate trending metrics. Returns number of rows updated."""
        # Reset daily counts (run daily)
        await self._db.execute(
            """
            UPDATE trending_queries
            SET searches_today = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE last_used < datetime('now', '-1 day')
            """
        )
        # Reset weekly counts
        await self._db.execute(
            """
            UPDATE trending_queries
            SET searches_week = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE last_used < datetime('now', '-7 days')
            """
        )
        # Reset monthly counts
        await self._db.execute(
            """
            UPDATE trending_queries
            SET searches_month = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE last_used < datetime('now', '-30 days')
            """
        )
        # Update popularity score: 0.4 * frequency + 0.3 * recent + 0.2 * growth + 0.1 * recency
        await self._db.execute(
            """
            UPDATE trending_queries
            SET popularity_score = (
                0.4 * CAST(frequency AS REAL) / (SELECT MAX(frequency) FROM trending_queries) +
                0.3 * CAST(searches_today AS REAL) / CASE WHEN MAX(searches_today) = 0 THEN 1 ELSE (SELECT MAX(searches_today) FROM trending_queries) END +
                0.2 * growth_rate +
                0.1 * (julianday('now') - julianday(last_used))
            ),
            updated_at = CURRENT_TIMESTAMP
            """
        )
        # Calculate growth rate based on frequency change
        await self._db.execute(
            """
            UPDATE trending_queries
            SET growth_rate = CAST(searches_today AS REAL) /
                            CASE WHEN searches_week = 0 THEN 1 ELSE CAST(searches_week AS REAL) / 7 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE searches_week > 0
            """
        )
        await self._db.commit()
        # Return count of updated rows
        result = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM trending_queries"
        )
        return result["count"] if result else 0

    # ------------------------------------------------------------------ #
    # Search suggestions
    # ------------------------------------------------------------------ #

    async def save_suggestion(
        self, query: str, suggestion: str, suggestion_type: str, score: float
    ) -> None:
        """Save or update a search suggestion."""
        await self._db.execute(
            """
            INSERT INTO search_suggestions (query, suggestion, type, score, frequency, last_used)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(query, suggestion, type) DO UPDATE SET
                score = excluded.score,
                frequency = frequency + 1,
                last_used = excluded.last_used
            """,
            (query, suggestion, suggestion_type, score, datetime.now().isoformat()),
        )
        await self._db.commit()

    async def get_suggestions(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get suggestions for a query."""
        rows = await self._db.fetchall(
            """
            SELECT suggestion, type, score, frequency, last_used
            FROM search_suggestions
            WHERE query = ?
            ORDER BY score DESC, frequency DESC, last_used DESC
            LIMIT ?
            """,
            (query, limit),
        )
        return [dict(row) for row in rows]

    async def get_suggestions_by_type(
        self, query: str, suggestion_type: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get suggestions filtered by type."""
        rows = await self._db.fetchall(
            """
            SELECT suggestion, type, score, frequency, last_used
            FROM search_suggestions
            WHERE query = ? AND type = ?
            ORDER BY score DESC, frequency DESC
            LIMIT ?
            """,
            (query, suggestion_type, limit),
        )
        return [dict(row) for row in rows]

    async def delete_suggestions(self, query: str) -> None:
        """Delete all suggestions for a query."""
        await self._db.execute(
            "DELETE FROM search_suggestions WHERE query = ?",
            (query,),
        )
        await self._db.commit()

    # ------------------------------------------------------------------ #
    # Related searches
    # ------------------------------------------------------------------ #

    async def add_related_search(
        self, query: str, related_query: str, score: float = 0.0
    ) -> None:
        """Add or update a related search relationship."""
        await self._db.execute(
            """
            INSERT INTO related_searches (query, related_query, co_occurrence_count, score, last_used)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(query, related_query) DO UPDATE SET
                co_occurrence_count = co_occurrence_count + 1,
                score = excluded.score,
                last_used = excluded.last_used
            """,
            (query, related_query, score, datetime.now().isoformat()),
        )
        await self._db.commit()

    async def get_related_searches(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get related searches for a query."""
        rows = await self._db.fetchall(
            """
            SELECT related_query, co_occurrence_count, click_count, score, last_used
            FROM related_searches
            WHERE query = ?
            ORDER BY score DESC, co_occurrence_count DESC, last_used DESC
            LIMIT ?
            """,
            (query, limit),
        )
        return [dict(row) for row in rows]

    async def increment_related_search_clicks(self, query: str, related_query: str) -> None:
        """Increment click count for a related search."""
        await self._db.execute(
            """
            UPDATE related_searches
            SET click_count = click_count + 1,
                score = score + 0.1,
                last_used = ?
            WHERE query = ? AND related_query = ?
            """,
            (datetime.now().isoformat(), query, related_query),
        )
        await self._db.commit()

    async def rebuild_related_searches(self, min_co_occurrence: int = 2) -> int:
        """Rebuild related searches from analytics. Returns number of relationships."""
        # Find co-occurring queries from search sessions
        await self._db.execute(
            """
            INSERT INTO related_searches (query, related_query, co_occurrence_count,
                                         score, last_used)
            SELECT
                s1.query as query,
                s2.query as related_query,
                COUNT(*) as co_occurrence_count,
                COUNT(*) * 0.5 as score,
                MAX(s1.timestamp) as last_used
            FROM search_analytics s1
            INNER JOIN search_analytics s2
                ON s1.session_id = s2.session_id
                AND s1.id < s2.id
                AND s1.query != s2.query
            WHERE s1.timestamp > datetime('now', '-30 days')
            GROUP BY s1.query, s2.query
            HAVING COUNT(*) >= ?
            ON CONFLICT(query, related_query) DO UPDATE SET
                co_occurrence_count = excluded.co_occurrence_count,
                score = excluded.score,
                last_used = excluded.last_used
            """,
            (min_co_occurrence,),
        )
        await self._db.commit()
        result = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM related_searches"
        )
        return result["count"] if result else 0

    # ------------------------------------------------------------------ #
    # Search analytics
    # ------------------------------------------------------------------ #

    async def record_search(
        self,
        query: str,
        user_id: int | None,
        session_id: str,
        clicked_result_id: int | None = None,
        response_time_ms: int | None = None,
        result_count: int = 0,
        autocomplete_used: bool = False,
    ) -> None:
        """Record a search event for analytics."""
        await self._db.execute(
            """
            INSERT INTO search_analytics
                (query, user_id, session_id, clicked_result_id,
                 response_time_ms, result_count, autocomplete_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                query,
                user_id,
                session_id,
                clicked_result_id,
                response_time_ms,
                result_count,
                autocomplete_used,
            ),
        )
        await self._db.commit()

    async def get_user_search_history(
        self, user_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recent search history for a user."""
        rows = await self._db.fetchall(
            """
            SELECT DISTINCT query, COUNT(*) as frequency, MAX(timestamp) as last_used
            FROM search_analytics
            WHERE user_id = ?
            GROUP BY query
            ORDER BY last_used DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [dict(row) for row in rows]

    async def get_session_searches(self, session_id: str) -> list[str]:
        """Get all queries from a session."""
        rows = await self._db.fetchall(
            """
            SELECT DISTINCT query
            FROM search_analytics
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        )
        return [row["query"] for row in rows]

    # ------------------------------------------------------------------ #
    # User preferences
    # ------------------------------------------------------------------ #

    async def get_user_preferences(self, user_id: int) -> dict[str, Any] | None:
        """Get user search preferences."""
        row = await self._db.fetchone(
            """
            SELECT preferred_categories, frequent_queries, personalization_enabled
            FROM user_search_preferences
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return dict(row) if row else None

    async def upsert_user_preferences(
        self,
        user_id: int,
        preferred_categories: str = "[]",
        frequent_queries: str = "[]",
        personalization_enabled: bool = True,
    ) -> None:
        """Update or insert user preferences."""
        await self._db.execute(
            """
            INSERT INTO user_search_preferences
                (user_id, preferred_categories, frequent_queries, personalization_enabled)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_categories = excluded.preferred_categories,
                frequent_queries = excluded.frequent_queries,
                personalization_enabled = excluded.personalization_enabled,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, preferred_categories, frequent_queries, personalization_enabled),
        )
        await self._db.commit()

    async def get_top_queries(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get top queries across all time."""
        rows = await self._db.fetchall(
            """
            SELECT query, COUNT(*) as frequency, COUNT(DISTINCT user_id) as unique_users,
                   COUNT(DISTINCT session_id) as sessions,
                   MAX(timestamp) as last_used
            FROM search_analytics
            GROUP BY query
            ORDER BY frequency DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]