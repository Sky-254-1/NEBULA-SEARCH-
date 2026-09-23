"""Scheduler for incremental re-indexing scans."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)

logger = logging.getLogger("nebula.incremental.scheduler")


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    name: str
    cron_expression: str
    interval_seconds: Optional[int]
    is_active: bool
    last_run: Optional[str]
    next_run: Optional[str]
    callback: Optional[Callable] = None


class IncrementalScheduler:
    """
    Schedules periodic incremental re-indexing scans.
    
    Supports cron expressions, fixed intervals, and manual triggers.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize scheduler."""
        self._config = config or get_incremental_config()
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start scheduler."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._schedule_loop())
        
        logger.info("Incremental scheduler started")
    
    async def stop(self) -> None:
        """Stop scheduler."""
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Incremental scheduler stopped")
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        is_active: bool = True,
    ) -> ScheduledTask:
        """
        Add scheduled task.
        
        Args:
            name: Task name
            callback: Async function to call
            cron_expression: Cron expression (e.g., "0 * * * *")
            interval_seconds: Interval in seconds (alternative to cron)
            is_active: Whether task is active
            
        Returns:
            ScheduledTask
        """
        task_id = name.lower().replace(" ", "_")
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            cron_expression=cron_expression or "",
            interval_seconds=interval_seconds,
            is_active=is_active,
            last_run=None,
            next_run=None,
            callback=callback,
        )
        
        self._tasks[task_id] = task
        
        logger.info(
            "Added scheduled task: %s (cron=%s, interval=%s)",
            name, cron_expression, interval_seconds
        )
        
        return task
    
    async def _schedule_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            try:
                now = datetime.now()
                
                for task_id, task in self._tasks.items():
                    if not task.is_active:
                        continue
                    
                    # Check if task should run
                    if self._should_run(task, now):
                        # Run task in background
                        asyncio.create_task(self._run_task(task_id))
                        
                        # Update last run
                        task.last_run = now.isoformat()
                        
                        # Calculate next run
                        task.next_run = self._calculate_next_run(task, now)
                
                # Sleep for a minute before checking again
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Scheduler loop error: %s", exc)
                await asyncio.sleep(60)
    
    def _should_run(self, task: ScheduledTask, now: datetime) -> bool:
        """
        Check if task should run now.
        
        Args:
            task: Scheduled task
            now: Current datetime
            
        Returns:
            True if task should run
        """
        if not task.is_active:
            return False
        
        # If no last run, run immediately
        if not task.last_run:
            return True
        
        # Check interval
        if task.interval_seconds:
            last_run = datetime.fromisoformat(task.last_run)
            elapsed = (now - last_run).total_seconds()
            return elapsed >= task.interval_seconds
        
        # TODO: Implement cron expression parsing
        if task.cron_expression:
            # Simplified cron check - would need proper cron parser
            return False
        
        return False
    
    def _calculate_next_run(self, task: ScheduledTask, now: datetime) -> str:
        """
        Calculate next run time.
        
        Args:
            task: Scheduled task
            now: Current datetime
            
        Returns:
            ISO format datetime string
        """
        if task.interval_seconds:
            from datetime import timedelta
            next_run = now + timedelta(seconds=task.interval_seconds)
            return next_run.isoformat()
        
        # Default to 1 hour
        from datetime import timedelta
        next_run = now + timedelta(hours=1)
        return next_run.isoformat()
    
    async def _run_task(self, task_id: str) -> None:
        """
        Execute scheduled task.
        
        Args:
            task_id: Task identifier
        """
        task = self._tasks.get(task_id)
        
        if not task or not task.callback:
            return
        
        try:
            logger.info("Running scheduled task: %s", task.name)
            
            # Execute callback
            result = task.callback()
            
            # Handle both sync and async callbacks
            if asyncio.iscoroutine(result):
                await result
            
            logger.info("Scheduled task completed: %s", task.name)
            
        except Exception as exc:
            logger.error("Scheduled task failed: %s - %s", task.name, exc)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled tasks.
        
        Returns:
            List of task dictionaries
        """
        return [
            {
                "task_id": task.task_id,
                "name": task.name,
                "cron_expression": task.cron_expression,
                "interval_seconds": task.interval_seconds,
                "is_active": task.is_active,
                "last_run": task.last_run,
                "next_run": task.next_run,
            }
            for task in self._tasks.values()
        ]
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task dict or None
        """
        task = self._tasks.get(task_id)
        
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "cron_expression": task.cron_expression,
            "interval_seconds": task.interval_seconds,
            "is_active": task.is_active,
            "last_run": task.last_run,
            "next_run": task.next_run,
        }
    
    async def run_now(self, task_id: str) -> bool:
        """
        Trigger task to run immediately.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was triggered
        """
        task = self._tasks.get(task_id)
        
        if not task:
            return False
        
        asyncio.create_task(self._run_task(task_id))
        return True
    
    def enable_task(self, task_id: str) -> bool:
        """
        Enable scheduled task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if enabled
        """
        task = self._tasks.get(task_id)
        
        if task:
            task.is_active = True
            return True
        
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """
        Disable scheduled task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if disabled
        """
        task = self._tasks.get(task_id)
        
        if task:
            task.is_active = False
            return True
        
        return False


def get_scheduler(config: Optional[IncrementalConfig] = None) -> IncrementalScheduler:
    """
    Get global scheduler instance.
    
    Args:
        config: Incremental config
        
    Returns:
        IncrementalScheduler instance
    """
    # Singleton pattern
    if not hasattr(get_scheduler, "_instance"):
        get_scheduler._instance = IncrementalScheduler(config)
    
    return get_scheduler._instance