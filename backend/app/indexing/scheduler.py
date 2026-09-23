"""Scheduler for automated indexing tasks."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Coroutine, Optional


logger = logging.getLogger("nebula.indexing.scheduler")


class ScheduleType(str, Enum):
    """Scheduler types."""
    MANUAL = "manual"
    INTERVAL = "interval"
    CRON = "cron"


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    name: str
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    is_active: bool = True
    last_run: Optional[float] = None
    next_run: Optional[float] = None


class IndexingScheduler:
    """Manages scheduled indexing tasks."""
    
    def __init__(self) -> None:
        self._scheduled_tasks: dict[str, SchedulerConfig] = {}
        self._running = False
        self._loop_task: Optional[Coroutine] = None
        self._callbacks: dict[str, Callable] = {}
    
    def register_task(
        self,
        name: str,
        schedule_type: ScheduleType,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> SchedulerConfig:
        """
        Register a scheduled task.
        
        Args:
            name: Task name
            schedule_type: Type of schedule
            interval_seconds: Interval in seconds (for interval type)
            cron_expression: Cron expression (for cron type)
            callback: Async function to call
            
        Returns:
            SchedulerConfig
        """
        config = SchedulerConfig(
            name=name,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
        )
        
        self._scheduled_tasks[name] = config
        if callback:
            self._callbacks[name] = callback
        
        # Calculate next run
        if schedule_type == ScheduleType.INTERVAL and interval_seconds:
            config.next_run = time.time() + interval_seconds
        elif schedule_type == ScheduleType.CRON and cron_expression:
            config.next_run = self._calculate_next_cron(cron_expression)
        
        logger.info("Registered scheduled task: %s (type=%s)", name, schedule_type)
        return config
    
    def _calculate_next_cron(self, cron_expression: str) -> float:
        """
        Calculate next run time from cron expression (simplified).
        
        Args:
            cron_expression: Cron expression (e.g., "0 2 * * *" for 2 AM daily)
            
        Returns:
            Next run timestamp
        """
        # Simplified cron parsing - supports daily at hour:minute
        # Format: "minute hour * * *"
        try:
            parts = cron_expression.split()
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                
                now = datetime.now()
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                return next_run.timestamp()
        except Exception as exc:
            logger.debug("Schedule calculation failed: %s", exc)
        
        # Default: run in 1 hour
        return time.time() + 3600
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._loop_task = asyncio.create_task(self._schedule_loop())
        logger.info("Scheduler started with %d tasks", len(self._scheduled_tasks))
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def _schedule_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = time.time()
            
            for name, config in self._scheduled_tasks.items():
                if not config.is_active:
                    continue
                
                if config.next_run and now >= config.next_run:
                    # Execute task
                    await self._execute_task(name, config)
                    
                    # Schedule next run
                    if config.schedule_type == ScheduleType.INTERVAL and config.interval_seconds:
                        config.next_run = now + config.interval_seconds
                    elif config.schedule_type == ScheduleType.CRON and config.cron_expression:
                        config.next_run = self._calculate_next_cron(config.cron_expression)
                    
                    config.last_run = now
            
            # Check every minute
            await asyncio.sleep(60)
    
    async def _execute_task(self, name: str, config: SchedulerConfig) -> None:
        """
        Execute a scheduled task.
        
        Args:
            name: Task name
            config: Scheduler config
        """
        logger.info("Executing scheduled task: %s", name)
        
        if name not in self._callbacks:
            logger.warning("No callback for task: %s", name)
            return
        
        try:
            callback = self._callbacks[name]
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
            
            logger.info("Scheduled task completed: %s", name)
        except Exception as exc:
            logger.error("Scheduled task failed: %s - %s", name, exc)
    
    async def run_task_now(self, name: str) -> bool:
        """
        Manually trigger a task.
        
        Args:
            name: Task name
            
        Returns:
            True if executed
        """
        if name not in self._scheduled_tasks:
            logger.warning("Task not found: %s", name)
            return False
        
        config = self._scheduled_tasks[name]
        await self._execute_task(name, config)
        return True
    
    def get_task_status(self, name: str) -> Optional[dict]:
        """
        Get task status.
        
        Args:
            name: Task name
            
        Returns:
            Task status dict or None
        """
        config = self._scheduled_tasks.get(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "schedule_type": config.schedule_type.value,
            "is_active": config.is_active,
            "last_run": datetime.fromtimestamp(config.last_run).isoformat() if config.last_run else None,
            "next_run": datetime.fromtimestamp(config.next_run).isoformat() if config.next_run else None,
        }
    
    def get_all_tasks(self) -> list[dict]:
        """Get all scheduled tasks."""
        return [
            {
                "name": config.name,
                "schedule_type": config.schedule_type.value,
                "is_active": config.is_active,
                "last_run": datetime.fromtimestamp(config.last_run).isoformat() if config.last_run else None,
                "next_run": datetime.fromtimestamp(config.next_run).isoformat() if config.next_run else None,
            }
            for config in self._scheduled_tasks.values()
        ]
    
    async def trigger_nightly_reindex(self) -> None:
        """Trigger nightly reindex of all documents that are stale or failed."""
        logger.info("Triggering nightly reindex")
        try:
            from app.database.engine import connect
            from app.indexing.tasks import submit_index_task

            db = await connect()
            try:
                # Select documents that are either failed or have never been indexed
                rows = await db.fetchall(
                    "SELECT id, user_id, filename, storage_path FROM documents "
                    "WHERE status IN ('failed', 'pending') OR indexed_at IS NULL"
                )
                queued = 0
                for row in rows:
                    try:
                        await submit_index_task(
                            document_id=row["id"],
                            user_id=row["user_id"],
                            filename=row["filename"],
                            file_path=row["storage_path"],
                        )
                        queued += 1
                    except Exception as exc:
                        logger.warning(
                            "Failed to queue document %d for reindex: %s", row["id"], exc
                        )
                logger.info("Nightly reindex: queued %d documents", queued)
            finally:
                await db.close()
        except Exception as exc:
            logger.error("Nightly reindex failed: %s", exc)

    async def trigger_weekly_optimization(self) -> None:
        """Trigger weekly optimization: aggregate analytics and clean up stale data."""
        logger.info("Triggering weekly optimization")
        try:
            from datetime import datetime, timedelta
            from app.database.engine import connect
            from app.database.repositories.analytics_repository import AnalyticsRepository

            db = await connect()
            try:
                analytics_repo = AnalyticsRepository(db)

                # Aggregate the past 7 days into daily summary tables
                today = datetime.utcnow().date()
                for days_back in range(1, 8):
                    day = datetime.combine(
                        today - timedelta(days=days_back), datetime.min.time()
                    )
                    try:
                        await analytics_repo.aggregate_daily(day)
                    except Exception as exc:
                        logger.warning("Failed to aggregate day %s: %s", day.date(), exc)

                # Remove search events older than 90 days to keep the table lean
                from app.config import get_settings
                settings = get_settings()
                if settings.uses_postgres:
                    await db.execute(
                        "DELETE FROM search_events WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days'"
                    )
                else:
                    await db.execute(
                        "DELETE FROM search_events WHERE created_at < datetime('now', '-90 days')"
                    )
                await db.commit()

                logger.info("Weekly optimization completed: analytics aggregated and old events pruned")
            finally:
                await db.close()
        except Exception as exc:
            logger.error("Weekly optimization failed: %s", exc)

    async def scan_missing_documents(self) -> None:
        """Scan documents table for entries that lack index records and queue them."""
        logger.info("Scanning for missing documents")
        try:
            from app.database.engine import connect
            from app.indexing.tasks import submit_index_task

            db = await connect()
            try:
                # Find documents marked 'indexed' but with no corresponding chunk records
                rows = await db.fetchall(
                    """
                    SELECT d.id, d.user_id, d.filename, d.storage_path
                    FROM documents d
                    LEFT JOIN document_chunks dc ON dc.document_id = d.id
                    WHERE d.status = 'indexed' AND dc.document_id IS NULL
                    """
                )
                queued = 0
                for row in rows:
                    try:
                        # Reset status so the worker will re-index it
                        await db.execute(
                            "UPDATE documents SET status = 'pending', indexed_at = NULL WHERE id = ?",
                            (row["id"],),
                        )
                        await submit_index_task(
                            document_id=row["id"],
                            user_id=row["user_id"],
                            filename=row["filename"],
                            file_path=row["storage_path"],
                        )
                        queued += 1
                    except Exception as exc:
                        logger.warning(
                            "Failed to queue missing document %d: %s", row["id"], exc
                        )
                await db.commit()
                logger.info("Scan complete: found and queued %d missing documents", queued)
            finally:
                await db.close()
        except Exception as exc:
            logger.error("Scan for missing documents failed: %s", exc)


# Global scheduler instance
scheduler = IndexingScheduler()


def get_scheduler() -> IndexingScheduler:
    """Get global scheduler instance."""
    return scheduler