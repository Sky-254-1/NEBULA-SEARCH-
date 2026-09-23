"""Analytics service layer for search analytics business logic."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Any

from app.database.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics business logic."""

    def __init__(self, db, redis_client=None):
        self._repo = AnalyticsRepository(db)
        self._redis = redis_client
        self._cache_ttl = 300  # 5 minutes

    async def record_search(
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
        """Record a search event."""
        try:
            event_id = await self._repo.record_search_event(
                query=query,
                user_id=user_id,
                session_id=session_id,
                search_backend=search_backend,
                search_type=search_type,
                results_count=results_count,
                response_time_ms=response_time_ms,
                clicked_result=clicked_result,
                device=device,
            )
            # Invalidate relevant caches
            await self._invalidate_cache("dashboard")
            await self._invalidate_cache("popular")
            return event_id
        except Exception:
            logger.exception("Failed to record search event")
            raise

    async def record_click(
        self,
        search_event_id: int,
        query: str,
        document_id: int,
        rank_position: int,
        time_to_click: float | None,
        user_id: int | None,
    ) -> None:
        """Record a click event."""
        try:
            await self._repo.record_click_event(
                search_event_id=search_event_id,
                query=query,
                document_id=document_id,
                rank_position=rank_position,
                time_to_click=time_to_click,
                user_id=user_id,
            )
            await self._invalidate_cache("dashboard")
        except Exception:
            logger.exception("Failed to record click event")
            raise

    async def get_dashboard(self, period: str = "24h") -> dict[str, Any]:
        """Get dashboard overview with caching."""
        cache_key = f"analytics:dashboard:{period}"
        
        # Try cache first
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        # Get from repository
        data = await self._repo.get_dashboard_overview(period)
        
        # Add response times
        response_times = await self._repo.get_response_time_stats()
        data["response_times"] = response_times
        
        # Add popular searches
        popular = await self._repo.get_popular_queries(limit=10)
        data["popular_searches"] = popular
        
        # Add zero-result queries
        zero_results = await self._repo.get_zero_result_queries(limit=10)
        data["zero_result_queries"] = zero_results
        
        # Add query trends
        trends = await self._repo.get_query_trends(period="daily", days=30)
        data["query_trends"] = trends
        
        # Cache the result
        await self._set_cached(cache_key, data)
        
        return data

    async def get_popular(self, limit: int = 10, days: int = 30) -> list[dict]:
        """Get popular searches with caching."""
        cache_key = f"analytics:popular:{limit}:{days}"
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        data = await self._repo.get_popular_queries(limit=limit, days=days)
        
        await self._set_cached(cache_key, data)
        return data

    async def get_zero_results(self, limit: int = 10, days: int = 30) -> list[dict]:
        """Get zero-result searches."""
        cache_key = f"analytics:zero_results:{limit}:{days}"
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        data = await self._repo.get_zero_result_queries(limit=limit, days=days)
        
        await self._set_cached(cache_key, data)
        return data

    async def get_response_times(self, days: int = 7) -> dict[str, float]:
        """Get response time analytics."""
        cache_key = f"analytics:response_times:{days}"
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        data = await self._repo.get_response_time_stats(days=days)
        
        await self._set_cached(cache_key, data)
        return data

    async def get_query_trends(self, period: str = "daily", days: int = 30) -> list[dict]:
        """Get query trends."""
        cache_key = f"analytics:trends:{period}:{days}"
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        data = await self._repo.get_query_trends(period=period, days=days)
        
        await self._set_cached(cache_key, data)
        return data

    async def get_user_analytics(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """Get user-specific analytics."""
        return await self._repo.get_user_analytics(user_id, days)

    async def get_click_analytics(self, days: int = 7) -> dict[str, Any]:
        """Get click analytics."""
        cache_key = f"analytics:clicks:{days}"
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        data = await self._repo.get_click_analytics(days)
        
        await self._set_cached(cache_key, data)
        return data

    async def calculate_ctr(self, days: int = 7) -> float:
        """Calculate click-through rate."""
        overview = await self._repo.get_dashboard_overview(period="7d")
        return overview.get("click_through_rate", 0.0)

    async def calculate_percentiles(self, values: list[float], percentiles: list[float]) -> dict[str, float]:
        """Calculate percentiles for response times."""
        if not values:
            return {f"p{p}": 0.0 for p in percentiles}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        result = {}
        for p in percentiles:
            k = (p / 100.0) * (n - 1)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                result[f"p{p}"] = sorted_values[int(k)]
            else:
                result[f"p{p}"] = sorted_values[int(f)] * (c - k) + sorted_values[int(c)] * (k - f)
        
        return result

    async def aggregate_hourly(self, date: datetime) -> None:
        """Aggregate hourly statistics."""
        try:
            await self._repo.aggregate_hourly(date)
            logger.info("Hourly aggregation completed for %s", date.replace(minute=0, second=0, microsecond=0))
        except Exception:
            logger.exception("Hourly aggregation failed for %s", date)

    async def aggregate_daily(self, date: datetime) -> None:
        """Aggregate daily statistics."""
        try:
            await self._repo.aggregate_daily(date)
            logger.info("Daily aggregation completed for %s", date.date())
        except Exception:
            logger.exception("Daily aggregation failed for %s", date.date())

    async def aggregate_weekly(self, date: datetime) -> None:
        """Aggregate weekly statistics."""
        try:
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=7)
            
            # Get stats for the week
            stats = await self._repo._db.fetchone(
                """SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
                    AVG(response_time_ms) as avg_response_time
                FROM search_events 
                WHERE created_at >= ? AND created_at < ?""",
                (start_of_week.isoformat(), end_of_week.isoformat()),
            )
            
            if stats:
                logger.info(
                    "Weekly aggregation: %d queries, %d users",
                    stats["total_queries"],
                    stats["unique_users"],
                )
        except Exception:
            logger.exception("Weekly aggregation failed")

    async def aggregate_monthly(self, date: datetime) -> None:
        """Aggregate monthly statistics."""
        try:
            start_of_month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end_of_month = start_of_month.replace(year=date.year + 1, month=1)
            else:
                end_of_month = start_of_month.replace(month=date.month + 1)
            
            # Get stats for the month
            stats = await self._repo._db.fetchone(
                """SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) as zero_results,
                    AVG(response_time_ms) as avg_response_time
                FROM search_events 
                WHERE created_at >= ? AND created_at < ?""",
                (start_of_month.isoformat(), end_of_month.isoformat()),
            )
            
            if stats:
                logger.info(
                    "Monthly aggregation: %d queries, %d users",
                    stats["total_queries"],
                    stats["unique_users"],
                )
        except Exception:
            logger.exception("Monthly aggregation failed")

    async def _get_cached(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._redis:
            return None
        try:
            import json
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception:
            logger.debug("Cache get failed for %s", key)
        return None

    async def _set_cached(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        if not self._redis:
            return
        try:
            import json
            ttl = ttl or self._cache_ttl
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            logger.debug("Cache set failed for %s", key)

    async def _invalidate_cache(self, pattern: str) -> None:
        """Invalidate cache by pattern."""
        if not self._redis:
            return
        try:
            keys = await self._redis.keys(f"analytics:{pattern}:*")
            if keys:
                await self._redis.delete(*keys)
        except Exception:
            logger.debug("Cache invalidation failed for pattern %s", pattern)