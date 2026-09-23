"""Background aggregation workers for analytics."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.database.engine import connect, DatabaseConnection
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger("nebula.analytics.background")


async def _get_db() -> DatabaseConnection:
    """Get database connection."""
    return await connect()


async def aggregate_hourly_stats() -> None:
    """Aggregate hourly statistics."""
    try:
        db = await _get_db()
        try:
            service = AnalyticsService(db, redis_client=None)
            # Aggregate for the previous hour
            previous_hour = datetime.now() - timedelta(hours=1)
            await service.aggregate_hourly(previous_hour)
            logger.debug("Hourly aggregation completed")
        finally:
            await db.close()
    except Exception:
        logger.exception("Hourly aggregation failed")


async def aggregate_daily_stats() -> None:
    """Aggregate daily statistics."""
    try:
        db = await _get_db()
        try:
            service = AnalyticsService(db, redis_client=None)
            # Aggregate for the previous day
            yesterday = datetime.now() - timedelta(days=1)
            await service.aggregate_daily(yesterday)
            logger.info("Daily aggregation completed")
        finally:
            await db.close()
    except Exception:
        logger.exception("Daily aggregation failed")


async def aggregate_weekly_stats() -> None:
    """Aggregate weekly statistics."""
    try:
        db = await _get_db()
        try:
            service = AnalyticsService(db, redis_client=None)
            # Aggregate for the previous week
            last_week = datetime.now() - timedelta(weeks=1)
            await service.aggregate_weekly(last_week)
            logger.info("Weekly aggregation completed")
        finally:
            await db.close()
    except Exception:
        logger.exception("Weekly aggregation failed")


async def aggregate_monthly_stats() -> None:
    """Aggregate monthly statistics."""
    try:
        db = await _get_db()
        try:
            service = AnalyticsService(db, redis_client=None)
            # Aggregate for the previous month
            last_month = datetime.now() - timedelta(days=30)
            await service.aggregate_monthly(last_month)
            logger.info("Monthly aggregation completed")
        finally:
            await db.close()
    except Exception:
        logger.exception("Monthly aggregation failed")


async def compute_trending_searches() -> None:
    """Compute trending searches and update query_trends table."""
    try:
        db = await _get_db()
        try:
            repo = db
            # Get top queries from the last 24 hours
            from app.config import get_settings
            settings = get_settings()
            if settings.uses_postgres:
                rows = await repo.fetchall(
                    """SELECT query, COUNT(*) as count 
                    FROM search_events 
                    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                    GROUP BY query 
                    ORDER BY count DESC 
                    LIMIT 50"""
                )
            else:
                rows = await repo.fetchall(
                    """SELECT query, COUNT(*) as count 
                    FROM search_events 
                    WHERE created_at >= datetime('now', '-1 day')
                    GROUP BY query 
                    ORDER BY count DESC 
                    LIMIT 50"""
                )
            
            # Store trending queries
            now = datetime.now()
            for row in rows:
                query = row["query"]
                count = row["count"]
                score = count  # Simplified scoring
                
                await repo.execute(
                    """INSERT OR REPLACE INTO query_trends 
                    (query, category, score, period, date)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        query,
                        "trending",
                        score,
                        "daily",
                        now.strftime("%Y-%m-%d"),
                    ),
                )
            
            logger.debug("Trending searches computed: %d queries", len(rows))
        finally:
            await db.close()
    except Exception:
        logger.exception("Trending computation failed")


async def refresh_analytics_cache() -> None:
    """Refresh analytics cache with fresh data."""
    try:
        from app.services.cache import cache_service
        
        if not cache_service._redis:
            return
        
        # Pre-compute and cache popular queries
        db = await _get_db()
        try:
            service = AnalyticsService(db, redis_client=cache_service._redis)
            await service.get_popular(limit=100, days=30)
            await service.get_dashboard(period="24h")
            logger.debug("Analytics cache refreshed")
        finally:
            await db.close()
    except Exception:
        logger.exception("Cache refresh failed")


async def archive_old_analytics(days: int = 90) -> None:
    """Archive old analytics data."""
    try:
        db = await _get_db()
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # For very old data, we could move to archive tables
            # For now, we just log what would be archived
            count = await db.fetchone(
                """SELECT COUNT(*) as count FROM search_events 
                WHERE created_at < ?""",
                (cutoff_date,),
            )
            
            if count and count["count"] > 0:
                logger.info(
                    "Would archive %d search events older than %s",
                    count["count"],
                    cutoff_date,
                )
        finally:
            await db.close()
    except Exception:
        logger.exception("Archive failed")


async def cleanup_expired_logs(days: int = 90) -> None:
    """Remove expired raw analytics logs."""
    try:
        db = await _get_db()
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            await db.execute(
                """DELETE FROM search_events WHERE created_at < ?""",
                (cutoff_date,),
            )
            await db.commit()
            
            logger.info("Cleaned up old search events before %s", cutoff_date)
        finally:
            await db.close()
    except Exception:
        logger.exception("Log cleanup failed")


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class AnalyticsBackgroundWorker:
    """Background worker for analytics aggregation."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Analytics background worker started")

    async def stop(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Analytics background worker stopped")

    async def _run(self) -> None:
        """Main worker loop."""
        last_hourly = 0.0
        last_daily = 0.0
        last_weekly = 0.0
        last_monthly = 0.0
        last_trending = 0.0
        last_cache_refresh = 0.0
        
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                now = datetime.now()
                now_ts = now.timestamp()
                
                # Hourly aggregation - every hour
                if now_ts - last_hourly >= 3600:
                    await aggregate_hourly_stats()
                    last_hourly = now_ts
                
                # Daily aggregation - every day at midnight
                if now.hour == 0 and now_ts - last_daily >= 86400:
                    await aggregate_daily_stats()
                    await cleanup_expired_logs(days=90)
                    last_daily = now_ts
                
                # Weekly aggregation - every Sunday
                if now.weekday() == 6 and now_ts - last_weekly >= 604800:
                    await aggregate_weekly_stats()
                    last_weekly = now_ts
                
                # Monthly aggregation - first day of month
                if now.day == 1 and now_ts - last_monthly >= 2592000:
                    await aggregate_monthly_stats()
                    last_monthly = now_ts
                
                # Compute trending - every 6 hours
                if now_ts - last_trending >= 21600:
                    await compute_trending_searches()
                    last_trending = now_ts
                
                # Refresh cache - every 5 minutes
                if now_ts - last_cache_refresh >= 300:
                    await refresh_analytics_cache()
                    last_cache_refresh = now_ts
                
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Background worker error")


# Global worker instance
_analytics_worker = AnalyticsBackgroundWorker()


async def start_analytics_worker() -> None:
    """Start analytics background worker."""
    await _analytics_worker.start()


async def stop_analytics_worker() -> None:
    """Stop analytics background worker."""
    await _analytics_worker.stop()