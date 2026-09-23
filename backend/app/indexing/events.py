"""Event system for indexing notifications."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nebula.indexing.events")


class EventType(str, Enum):
    """Indexing event types."""
    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_RETRYING = "job.retrying"
    JOB_CANCELLED = "job.cancelled"
    WORKER_STARTED = "worker.started"
    WORKER_STOPPED = "worker.stopped"
    WORKER_DEAD = "worker.dead"
    QUEUE_PAUSED = "queue.paused"
    QUEUE_RESUMED = "queue.resumed"


@dataclass
class IndexingEvent:
    """Indexing event."""
    event_type: EventType
    job_id: Optional[str] = None
    worker_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Event bus for indexing events."""
    
    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[IndexingEvent] = []
        self._max_history = 1000
        self._async_subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to subscribe to
            callback: Sync callback function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug("Subscribed to event: %s", event_type)
    
    def subscribe_async(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type with async callback.
        
        Args:
            event_type: Event type to subscribe to
            callback: Async callback function
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(callback)
        logger.debug("Subscribed async to event: %s", event_type)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
        if event_type in self._async_subscribers:
            self._async_subscribers[event_type].remove(callback)
    
    async def emit(self, event: IndexingEvent) -> None:
        """
        Emit an event.
        
        Args:
            event: Event to emit
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Call sync subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as exc:
                    logger.error("Event subscriber error: %s", exc)
        
        # Call async subscribers
        if event.event_type in self._async_subscribers:
            tasks = []
            for callback in self._async_subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(event))
                    else:
                        callback(event)
                except Exception as exc:
                    logger.error("Async event subscriber error: %s", exc)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug("Emitted event: %s", event.event_type)
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        job_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[IndexingEvent]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            job_id: Filter by job ID
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if job_id:
            events = [e for e in events if e.job_id == job_id]
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Global event bus
event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get global event bus."""
    return event_bus


