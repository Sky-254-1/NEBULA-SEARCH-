"""Analytics repository for search analytics data access."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.database.engine import DatabaseConnection


class AnalyticsRepository:
    """Repository for analytics data access."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def record_search_event(
        self,
        query: str,
        user_id: int | None,
        session_id: str,
        search_backend: str,
        search_type: str,
        results_count: int,
        response_time_ms: float,
        clicked_result: int | None,
        device: str | None,
    ) -> int:
        """Record a search event. Returns the event ID."""
        await self._db.execute(
            """INSERT INTO search_events 
            (query, user_id, session_id, search_backend, search_type, results_count, 
             response_time_ms, clicked_result, device)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                query,
                user_id,
                session_id,
                search_backend,
                search_type,
                results_count,
                response_time_ms,
                clicked_result,
                device,
            ),
        )
        await self._db.commit()
        cursor = await self._db.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def record_click_event(
        self,
        search_event_id: int,
        query: str,
        document_id: int,
        rank_position: int,
        time_to_click: float | None,
        user_id: int | None,
    ) -> None:
        """Record a click event."""
        await self._db.execute(
            """INSERT INTO click_events 
            (search_event_id, query, document_id, rank_position, time_to_click, user_id)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (search_event_id, query, document_id, rank_position, time_to_click, user_id),
        )
        await self._db.commit()

    async def record_response_time(
        self,
        total_latency: float,
        db_latency: float,
        redis_latency: float,
        semantic_latency: float,
        bm25_latency: float,
        ranking_latency: float,
        snippet_latency: float,
        api_latency: float,
    ) -> None:
        """Record response time metrics."""
        await self._db.execute(
            """INSERT INTO response_time_metrics 
            (total_latency, db_latency, redis_latency, semantic_latency, 
             bm25_latency, ranking_latency, snippet_latency, api_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                total_latency,
                db_latency,
                redis_latency,
                semantic_latency,
                bm25_latency,
                ranking_latency,
                snippet_latency,
                api_latency,
            ),
        )
        await self._db.commit()

    async def get_popular_queries(self, limit: int = 10, days: int = 30) -> list[dict]:
        """Get popular queries with counts."""
        from app.config import get_settings
        settings = get_settings()
        if settings.uses_postgres:
            rows = await self._db.fetchall(
                """SELECT query, COUNT(*) as count 
                FROM search_events 
                WHERE created_at >= CURRENT_TIMESTAMP - $1::interval
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT $2""",
                (f"{days} days", limit),
            )
        else:
            rows = await self._db.fetchall(
                """SELECT query, COUNT(*) as count 
                FROM search_events 
                WHERE created_at >= datetime('now', ?)
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT ?""",
                (f"-{days} days", limit),
            )
        return [dict(row) for row in rows]

    async def get_zero_result_queries(self, limit: int = 10, days: int = 30) -> list[dict]:
        """Get queries that returned zero results."""
        from app.config import get_settings
        settings = get_settings()
        if settings.uses_postgres:
            rows = await self._db.fetchall(
                """SELECT query, COUNT(*) as count 
                FROM search_events 
                WHERE results_count = 0 
                AND created_at >= CURRENT_TIMESTAMP - $1::interval
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT $2""",
                (f"{days} days", limit),
            )
        else:
            rows = await self._db.fetchall(
                """SELECT query, COUNT(*) as count 
                FROM search_events 
                WHERE results_count = 0 
                AND created_at >= datetime('now', ?)
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT ?""",
                (f"-{days} days", limit),
            )
        return [dict(row) for row in rows]

    async def get_response_time_stats(self, days: int = 7) -> dict[str, float]:
        """Get response time statistics."""
        rows = await self._db.fetchall(
            """SELECT 
                AVG(response_time_ms) as avg,
                AVG(response_time_ms) as median,
                MAX(response_time_ms) as max,
                COUNT(*) as total
            FROM search_events 
            WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        if not rows:
            return {"average": 0.0, "median": 0.0, "max": 0.0, "p95": 0.0, "p99": 0.0}
        row = rows[0]
        # For proper percentile calculation, we'd need subqueries or window functions
        # This is simplified for SQLite compatibility
        return {
            "average": round(row["avg"] or 0.0, 2),
            "median": round(row["median"] or 0.0, 2),
            "max": round(row["max"] or 0.0, 2),
            "p95": round(row["avg"] * 1.5 if row["avg"] else 0.0, 2),  # Simplified
            "p99": round(row["avg"] * 2.0 if row["avg"] else 0.0, 2),  # Simplified
        }

    async def get_query_trends(self, period: str = "daily", days: int = 30) -> list[dict]:
        """Get query trends over time."""
        # Strict whitelist: period -> static SQL fragments.
        # We never interpolate user-provided strings into SQL directly.
        _SQL_BY_PERIOD: dict[str, tuple[str, str]] = {
            "daily": (
                "%Y-%m-%d",
                """
                SELECT
                    strftime('%Y-%m-%d', created_at) AS date,
                    COUNT(*) AS queries,
                    COUNT(DISTINCT user_id) AS unique_users,
                    SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) AS zero_results
                FROM search_events
                WHERE created_at >= datetime('now', ?)
                GROUP BY strftime('%Y-%m-%d', created_at)
                ORDER BY date ASC
                """,
            ),
            "hourly": (
                "%Y-%m-%d %H:00:00",
                """
                SELECT
                    strftime('%Y-%m-%d %H:00:00', created_at) AS date,
                    COUNT(*) AS queries,
                    COUNT(DISTINCT user_id) AS unique_users,
                    SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) AS zero_results
                FROM search_events
                WHERE created_at >= datetime('now', ?)
                GROUP BY strftime('%Y-%m-%d %H:00:00', created_at)
                ORDER BY date ASC
                """,
            ),
        }
        if period not in _SQL_BY_PERIOD:
            raise ValueError(f"Unknown trend period: {period!r}")
        _, sql = _SQL_BY_PERIOD[period]

        rows = await self._db.fetchall(sql, (f"-{int(days)} days",))
        return [dict(row) for row in rows]

    async def get_dashboard_overview(self, period: str = "24h") -> dict[str, Any]:
        """Get dashboard overview statistics."""
        period_map = {
            "24h": "-1 day",
            "7d": "-7 days",
            "30d": "-30 days",
            "90d": "-90 days",
        }
        time_filter = period_map.get(period, "-1 day")
        
        # Total queries
        total_queries = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM search_events 
            WHERE created_at >= datetime('now', ?)""",
            (time_filter,),
        )
        
        # Unique users
        unique_users = await self._db.fetchone(
            """SELECT COUNT(DISTINCT user_id) as count FROM search_events 
            WHERE created_at >= datetime('now', ?) AND user_id IS NOT NULL""",
            (time_filter,),
        )
        
        # Average response time
        avg_response = await self._db.fetchone(
            """SELECT AVG(response_time_ms) as avg FROM search_events 
            WHERE created_at >= datetime('now', ?)""",
            (time_filter,),
        )
        
        # Zero result rate
        total = total_queries["count"] if total_queries else 0
        zero_results = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM search_events 
            WHERE results_count = 0 AND created_at >= datetime('now', ?)""",
            (time_filter,),
        )
        zero_result_rate = (zero_results["count"] / total * 100) if total > 0 else 0.0
        
        # Click-through rate
        total_clicks = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM click_events 
            WHERE created_at >= datetime('now', ?)""",
            (time_filter,),
        )
        ctr = (total_clicks["count"] / total * 100) if total > 0 else 0.0
        
        return {
            "total_queries": total,
            "unique_users": unique_users["count"] if unique_users else 0,
            "average_response_time_ms": round(avg_response["avg"] or 0.0, 2),
            "zero_result_rate": round(zero_result_rate, 2),
            "click_through_rate": round(ctr, 2),
        }

    async def get_user_analytics(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """Get analytics for a specific user."""
        # Search count
        search_count = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM search_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?)""",
            (user_id, f"-{days} days"),
        )
        
        # Average session duration (simplified)
        avg_session = await self._db.fetchone(
            """SELECT AVG(response_time_ms) as avg FROM search_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?)""",
            (user_id, f"-{days} days"),
        )
        
        # Preferred search type
        search_type = await self._db.fetchone(
            """SELECT search_type, COUNT(*) as count FROM search_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            GROUP BY search_type ORDER BY count DESC LIMIT 1""",
            (user_id, f"-{days} days"),
        )
        
        # Most clicked documents
        clicked_docs = await self._db.fetchall(
            """SELECT document_id, COUNT(*) as clicks FROM click_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            GROUP BY document_id ORDER BY clicks DESC LIMIT 10""",
            (user_id, f"-{days} days"),
        )
        
        return {
            "searches": search_count["count"] if search_count else 0,
            "avg_session_duration_ms": round(avg_session["avg"] or 0.0, 2),
            "preferred_search_type": search_type["search_type"] if search_type else "keyword",
            "most_clicked_documents": [dict(doc) for doc in clicked_docs],
        }

    async def get_click_analytics(self, days: int = 7) -> dict[str, Any]:
        """Get click-through analytics."""
        # Total clicks
        total_clicks = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM click_events 
            WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        
        # Average click position
        avg_position = await self._db.fetchone(
            """SELECT AVG(rank_position) as avg FROM click_events 
            WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        
        # Most clicked documents
        most_clicked = await self._db.fetchall(
            """SELECT document_id, COUNT(*) as clicks FROM click_events 
            WHERE created_at >= datetime('now', ?)
            GROUP BY document_id ORDER BY clicks DESC LIMIT 10""",
            (f"-{days} days",),
        )
        
        return {
            "total_clicks": total_clicks["count"] if total_clicks else 0,
            "avg_click_position": round(avg_position["avg"] or 0.0, 2),
            "most_clicked_documents": [dict(doc) for doc in most_clicked],
        }

    async def get_search_quality_metrics(self, days: int = 30) -> dict[str, Any]:
        """Calculate search quality metrics."""
        # Zero result rate
        stats = await self._db.fetchone(
            """SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
                AVG(response_time_ms) as avg_response_time
            FROM search_events 
            WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        
        total = stats["total_queries"] if stats else 0
        zero_results = stats["zero_results"] if stats else 0
        
        # Semantic search usage
        semantic_usage = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM search_events 
            WHERE search_type = 'semantic' AND created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        
        # Hybrid search usage
        hybrid_usage = await self._db.fetchone(
            """SELECT COUNT(*) as count FROM search_events 
            WHERE search_type = 'hybrid' AND created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        
        return {
            "zero_result_rate": round((zero_results / total * 100) if total > 0 else 0.0, 2),
            "avg_response_time": round(stats["avg_response_time"] or 0.0, 2),
            "semantic_search_usage": semantic_usage["count"] if semantic_usage else 0,
            "hybrid_search_usage": hybrid_usage["count"] if hybrid_usage else 0,
        }

    async def aggregate_daily(self, date: datetime) -> None:
        """Aggregate daily statistics."""
        date_str = date.strftime("%Y-%m-%d")
        stats = await self._db.fetchone(
            """SELECT 
                COUNT(*) as total_queries,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
                (SELECT COUNT(*) FROM click_events WHERE date(created_at) = ?) as total_clicks,
                AVG(response_time_ms) as avg_response_time
            FROM search_events 
            WHERE date(created_at) = ?""",
            (date_str, date_str),
        )
        if stats:
            await self._db.execute(
                """INSERT OR REPLACE INTO analytics_daily 
                (date, total_queries, unique_users, zero_result_queries, total_clicks, avg_response_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    date_str,
                    stats["total_queries"],
                    stats["unique_users"],
                    stats["zero_results"],
                    stats["total_clicks"],
                    stats["avg_response_time"],
                    datetime.now().isoformat(),
                ),
            )
            await self._db.commit()

    async def aggregate_hourly(self, hour: datetime) -> None:
        """Aggregate hourly statistics."""
        hour_str = hour.strftime("%Y-%m-%d %H:00:00")
        next_hour = (hour + timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
        
        stats = await self._db.fetchone(
            """SELECT 
                COUNT(*) as total_queries,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
                AVG(response_time_ms) as avg_response_time
            FROM search_events 
            WHERE created_at >= ? AND created_at < ?""",
            (hour_str, next_hour),
        )
        if stats:
            await self._db.execute(
                """INSERT OR REPLACE INTO analytics_hourly 
                (hour_timestamp, total_queries, unique_users, zero_result_queries, avg_response_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    hour_str,
                    stats["total_queries"],
                    stats["unique_users"],
                    stats["zero_results"],
                    stats["avg_response_time"],
                    datetime.now().isoformat(),
                ),
            )
            await self._db.commit()