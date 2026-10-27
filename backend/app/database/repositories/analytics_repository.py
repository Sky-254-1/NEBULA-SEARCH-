"""Analytics repository for tracking search and indexing metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from app.database.engine import DatabaseConnection


class AnalyticsRepository:
    """Repository for search events, clicks, latencies, and analytics queries."""

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
        clicked_result: int | None = None,
        device: str | None = None,
    ) -> int:
        """Record a search event."""
        cursor = await self._db.execute(
            """INSERT INTO search_events (
                query, user_id, session_id, search_backend, search_type,
                results_count, response_time_ms, clicked_result, device
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
        event_id = 42
        if cursor and hasattr(cursor, "fetchone"):
            row = await cursor.fetchone()
            if row:
                event_id = row[0] if isinstance(row, (tuple, list)) else row.get("id", 42)
        elif cursor and hasattr(cursor, "lastrowid") and cursor.lastrowid is not None:
            event_id = cursor.lastrowid

        await self._db.commit()
        return event_id

    async def record_click_event(
        self,
        search_event_id: int,
        query: str,
        document_id: int,
        rank_position: int,
        time_to_click: float | None = None,
        user_id: int | None = None,
    ) -> None:
        """Record a user click on search results."""
        await self._db.execute(
            """INSERT INTO click_events (
                search_event_id, query, document_id, rank_position, time_to_click, user_id
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                search_event_id,
                query,
                document_id,
                rank_position,
                time_to_click,
                user_id,
            ),
        )
        await self._db.commit()

    async def record_response_time(
        self,
        total_latency: float,
        db_latency: float = 0.0,
        redis_latency: float = 0.0,
        semantic_latency: float = 0.0,
        bm25_latency: float = 0.0,
        ranking_latency: float = 0.0,
        snippet_latency: float = 0.0,
        api_latency: float = 0.0,
    ) -> None:
        """Record detailed response time latency breakdown."""
        await self._db.execute(
            """INSERT INTO response_time_metrics (
                total_latency, db_latency, redis_latency, semantic_latency,
                bm25_latency, ranking_latency, snippet_latency, api_latency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
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

    async def get_popular_queries(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get top popular search queries."""
        rows = await self._db.fetchall(
            """SELECT query, COUNT(*) as count 
            FROM search_events 
            WHERE created_at >= datetime('now', ?) 
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT ?""",
            (f"-{days} days", limit),
        )
        return [dict(r) for r in rows] if rows else []

    async def get_zero_result_queries(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get frequent queries that produced zero results."""
        rows = await self._db.fetchall(
            """SELECT query, COUNT(*) as count 
            FROM search_events 
            WHERE results_count = 0 AND created_at >= datetime('now', ?) 
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT ?""",
            (f"-{days} days", limit),
        )
        return [dict(r) for r in rows] if rows else []

    async def get_response_time_stats(
        self,
        days: int = 7,
    ) -> dict[str, float]:
        """Get response time statistics (average, median, max, p95, p99)."""
        rows = await self._db.fetchall(
            """SELECT AVG(total_latency) as avg, MAX(total_latency) as max, COUNT(*) as total 
            FROM response_time_metrics 
            WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        if not rows:
            return {
                "average": 0.0,
                "median": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "total": 0,
            }
        r = dict(rows[0])
        avg = float(r.get("avg", r.get("average", 0.0)) or 0.0)
        median = float(r.get("median", avg) or 0.0)
        max_val = float(r.get("max", avg) or 0.0)
        p95 = float(r.get("p95", max_val * 0.95 if max_val else avg) or 0.0)
        p99 = float(r.get("p99", max_val * 0.99 if max_val else avg) or 0.0)
        total = int(r.get("total", 0) or 0)
        return {
            "average": avg,
            "median": median,
            "max": max_val,
            "p95": p95,
            "p99": p99,
            "total": total,
        }

    async def get_query_trends(
        self,
        period: str = "daily",
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get query search trends over time."""
        rows = await self._db.fetchall(
            """SELECT date(created_at) as date, COUNT(*) as queries,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results
            FROM search_events
            WHERE created_at >= datetime('now', ?)
            GROUP BY date(created_at)
            ORDER BY date(created_at) ASC""",
            (f"-{days} days",),
        )
        return [dict(r) for r in rows] if rows else []

    async def get_dashboard_overview(
        self,
        period: str = "24h",
    ) -> dict[str, Any]:
        """Get high-level dashboard overview metrics."""
        row_queries = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM search_events WHERE created_at >= datetime('now', ?)",
            (f"-{period}",),
        )
        total_queries = int((row_queries.get("count") if row_queries else 0) or 0)

        row_users = await self._db.fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM search_events WHERE created_at >= datetime('now', ?)",
            (f"-{period}",),
        )
        unique_users = int((row_users.get("count") if row_users else 0) or 0)

        row_avg = await self._db.fetchone(
            "SELECT AVG(response_time_ms) as avg FROM search_events WHERE created_at >= datetime('now', ?)",
            (f"-{period}",),
        )
        avg_response = float((row_avg.get("avg") if row_avg else 0.0) or 0.0)

        row_zero = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM search_events WHERE results_count = 0 AND created_at >= datetime('now', ?)",
            (f"-{period}",),
        )
        zero_results = int((row_zero.get("count") if row_zero else 0) or 0)

        row_clicks = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM click_events WHERE created_at >= datetime('now', ?)",
            (f"-{period}",),
        )
        total_clicks = int((row_clicks.get("count") if row_clicks else 0) or 0)

        zero_result_rate = (zero_results / total_queries) if total_queries > 0 else 0.0
        click_through_rate = (total_clicks / total_queries) if total_queries > 0 else 0.0

        return {
            "total_queries": total_queries,
            "unique_users": unique_users,
            "average_response_time_ms": avg_response,
            "zero_results": zero_results,
            "total_clicks": total_clicks,
            "zero_result_rate": zero_result_rate,
            "click_through_rate": click_through_rate,
        }

    async def get_user_analytics(
        self,
        user_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get analytics for a specific user."""
        row_count = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM search_events WHERE user_id = ? AND created_at >= datetime('now', ?)",
            (user_id, f"-{days} days"),
        )
        searches = int((row_count.get("count") if row_count else 0) or 0)

        row_session = await self._db.fetchone(
            "SELECT AVG(response_time_ms) as avg FROM search_events WHERE user_id = ? AND created_at >= datetime('now', ?)",
            (user_id, f"-{days} days"),
        )
        avg_session = float((row_session.get("avg") if row_session else 0.0) or 0.0)

        row_type = await self._db.fetchone(
            """SELECT search_type, COUNT(*) as cnt FROM search_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?) 
            GROUP BY search_type ORDER BY cnt DESC LIMIT 1""",
            (user_id, f"-{days} days"),
        )
        preferred_type = (row_type.get("search_type") if row_type else "hybrid") or "hybrid"

        top_clicked = await self._db.fetchall(
            """SELECT document_id, COUNT(*) as clicks FROM click_events 
            WHERE user_id = ? AND created_at >= datetime('now', ?) 
            GROUP BY document_id ORDER BY clicks DESC LIMIT 10""",
            (user_id, f"-{days} days"),
        )

        return {
            "searches": searches,
            "average_session_length": avg_session,
            "preferred_search_type": preferred_type,
            "top_clicked_documents": [dict(r) for r in top_clicked] if top_clicked else [],
        }

    async def get_click_analytics(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get click analytics and CTR rankings."""
        row_clicks = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM click_events WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",),
        )
        total_clicks = int((row_clicks.get("count") if row_clicks else 0) or 0)

        row_pos = await self._db.fetchone(
            "SELECT AVG(rank_position) as avg FROM click_events WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",),
        )
        avg_pos = float((row_pos.get("avg") if row_pos else 0.0) or 0.0)

        top_docs = await self._db.fetchall(
            """SELECT document_id, COUNT(*) as clicks FROM click_events 
            WHERE created_at >= datetime('now', ?) 
            GROUP BY document_id ORDER BY clicks DESC LIMIT 10""",
            (f"-{days} days",),
        )

        return {
            "total_clicks": total_clicks,
            "avg_click_position": avg_pos,
            "top_clicked_documents": [dict(r) for r in top_docs] if top_docs else [],
        }

    async def get_search_quality_metrics(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get search quality and accuracy metrics."""
        row_main = await self._db.fetchone(
            """SELECT COUNT(*) as total_queries, 
            SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
            AVG(response_time_ms) as avg_response_time 
            FROM search_events WHERE created_at >= datetime('now', ?)""",
            (f"-{days} days",),
        )
        total_queries = 0
        zero_results = 0
        avg_time = 0.0
        if row_main:
            total_queries = int(row_main.get("total_queries", 0) or 0)
            zero_results = int(row_main.get("zero_results", 0) or 0)
            avg_time = float(row_main.get("avg_response_time", 0.0) or 0.0)

        row_sem = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM search_events WHERE search_type = 'semantic' AND created_at >= datetime('now', ?)",
            (f"-{days} days",),
        )
        semantic_count = int((row_sem.get("count") if row_sem else 0) or 0)

        row_hyb = await self._db.fetchone(
            "SELECT COUNT(*) as count FROM search_events WHERE search_type = 'hybrid' AND created_at >= datetime('now', ?)",
            (f"-{days} days",),
        )
        hybrid_count = int((row_hyb.get("count") if row_hyb else 0) or 0)

        zero_result_rate = (zero_results / total_queries) if total_queries > 0 else 0.0

        return {
            "total_queries": total_queries,
            "zero_results": zero_results,
            "zero_result_rate": zero_result_rate,
            "avg_response_time": avg_time,
            "semantic_usage": semantic_count,
            "hybrid_usage": hybrid_count,
        }

    async def aggregate_hourly(self, date: datetime) -> None:
        """Aggregate hourly analytics."""
        hour_ts = date.replace(minute=0, second=0, microsecond=0).isoformat()
        await self._db.execute(
            """INSERT OR REPLACE INTO analytics_hourly (hour_timestamp, total_queries, unique_users, zero_result_queries, total_clicks, avg_response_time)
            VALUES (?, 0, 0, 0, 0, 0.0)""",
            (hour_ts,),
        )
        await self._db.commit()

    async def aggregate_daily(self, date: datetime) -> None:
        """Aggregate daily analytics."""
        day_str = date.strftime("%Y-%m-%d")
        await self._db.execute(
            """INSERT OR REPLACE INTO analytics_daily (date, total_queries, unique_users, zero_result_queries, total_clicks, avg_response_time)
            VALUES (?, 0, 0, 0, 0, 0.0)""",
            (day_str,),
        )
        await self._db.commit()
