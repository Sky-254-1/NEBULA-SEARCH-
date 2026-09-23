"""Event system for incremental re-indexing."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger("nebula.incremental.events")


class IncrementalEventType(str, Enum):
    """Types of incremental re-indexing events."""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    CHANGE_DETECTED = "change_detected"
    DOCUMENT_NEW = "document_new"
    DOCUMENT_UNCHANGED = "document_unchanged"
    DOCUMENT_MODIFIED = "document_modified"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_RENAMED = "document_renamed"
    DOCUMENT_MOVED = "document_moved"
    DOCUMENT_CORRUPTED = "document_corrupted"
    CHUNK_ADDED = "chunk_added"
    CHUNK_REMOVED = "chunk_removed"
    CHUNK_MODIFIED = "chunk_modified"
    CHUNK_REUSED = "chunk_reused"
    EMBEDDING_GENERATED = "embedding_generated"
    EMBEDDING_REUSED = "embedding_reused"
    VECTOR_DELETED = "vector_deleted"
    METADATA_UPDATED = "metadata_updated"
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    CLEANUP_STARTED = "cleanup_started"
    CLEANUP_COMPLETED = "cleanup_completed"
    REINDEX_STARTED = "reindex_started"
    REINDEX_COMPLETED = "reindex_completed"


@dataclass
class IncrementalEvent:
    """Event data structure."""
    event_type: IncrementalEventType
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class EventHandler:
    """Base event handler."""
    
    async def handle(self, event: IncrementalEvent) -> None:
        """Handle event. Override in subclass."""
        pass


class EventManager:
    """
    Manages event publishing and subscription.
    
    Supports multiple handlers per event type with async execution.
    """

    def __init__(self) -> None:
        """Initialize event manager."""
        self._handlers: Dict[IncrementalEventType, List[Callable]] = {}
        self._history: List[IncrementalEvent] = []
        self._max_history = 1000
    
    def subscribe(
        self,
        event_type: IncrementalEventType,
        handler: Callable[[IncrementalEvent], Any],
    ) -> None:
        """
        Subscribe to event type.
        
        Args:
            event_type: Event type to listen for
            handler: Async or sync handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        
        logger.debug("Subscribed handler to %s", event_type)
    
    def unsubscribe(
        self,
        event_type: IncrementalEventType,
        handler: Callable[[IncrementalEvent], Any],
    ) -> None:
        """
        Unsubscribe from event type.
        
        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def publish(self, event: IncrementalEvent) -> None:
        """
        Publish event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Get handlers for this event type
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug("No handlers for event %s", event.event_type)
            return
        
        # Execute handlers
        logger.debug("Publishing event %s to %d handlers", event.event_type, len(handlers))
        
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, handler, event))
            except Exception as exc:
                logger.error("Error executing handler for %s: %s", event.event_type, exc)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(
        self,
        event_type: Optional[IncrementalEventType] = None,
        document_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[IncrementalEvent]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            document_id: Filter by document ID
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        events = self._history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if document_id:
            events = [e for e in events if e.document_id == document_id]
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()
        logger.debug("Cleared event history")


# Global event manager instance
_event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    """Get global event manager instance."""
    global _event_manager
    
    if _event_manager is None:
        _event_manager = EventManager()
    
    return _event_manager


def reset_event_manager() -> None:
    """Reset event manager (for testing)."""
    global _event_manager
    _event_manager = None


# Convenience functions
async def emit_event(event: IncrementalEvent) -> None:
    """Emit event to all subscribers."""
    manager = get_event_manager()
    await manager.publish(event)


async def emit_scan_started(document_id: int) -> None:
    """Emit scan started event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.SCAN_STARTED,
        document_id=document_id,
    ))


async def emit_scan_completed(document_id: int, duration_seconds: float) -> None:
    """Emit scan completed event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.SCAN_COMPLETED,
        document_id=document_id,
        duration_seconds=duration_seconds,
    ))


async def emit_change_detected(
    document_id: int,
    change_type: str,
    chunks_changed: int = 0,
) -> None:
    """Emit change detected event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.CHANGE_DETECTED,
        document_id=document_id,
        data={
            "change_type": change_type,
            "chunks_changed": chunks_changed,
        },
    ))


async def emit_chunk_operation(
    document_id: int,
    chunk_id: int,
    operation: str,
) -> None:
    """Emit chunk operation event."""
    event_type_map = {
        "add": IncrementalEventType.CHUNK_ADDED,
        "remove": IncrementalEventType.CHUNK_REMOVED,
        "modify": IncrementalEventType.CHUNK_MODIFIED,
        "reuse": IncrementalEventType.CHUNK_REUSED,
    }
    
    event_type = event_type_map.get(operation)
    if event_type:
        await emit_event(IncrementalEvent(
            event_type=event_type,
            document_id=document_id,
            chunk_id=chunk_id,
        ))


async def emit_embedding_generated(
    document_id: int,
    chunk_id: int,
) -> None:
    """Emit embedding generated event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.EMBEDDING_GENERATED,
        document_id=document_id,
        chunk_id=chunk_id,
    ))


async def emit_document_new(document_id: int) -> None:
    """Emit document new event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.DOCUMENT_NEW,
        document_id=document_id,
    ))


async def emit_document_modified(document_id: int) -> None:
    """Emit document modified event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.DOCUMENT_MODIFIED,
        document_id=document_id,
    ))


async def emit_document_unchanged(document_id: int) -> None:
    """Emit document unchanged event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.DOCUMENT_UNCHANGED,
        document_id=document_id,
    ))


async def emit_document_deleted(document_id: int) -> None:
    """Emit document deleted event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.DOCUMENT_DELETED,
        document_id=document_id,
    ))


async def emit_metadata_updated(document_id: int, fields: List[str]) -> None:
    """Emit metadata updated event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.METADATA_UPDATED,
        document_id=document_id,
        data={"fields": fields},
    ))


async def emit_sync_completed(document_id: int, duration_seconds: float) -> None:
    """Emit sync completed event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.SYNC_COMPLETED,
        document_id=document_id,
        duration_seconds=duration_seconds,
    ))


async def emit_cleanup_completed(
    deleted_vectors: int,
    deleted_chunks: int,
    duration_seconds: float,
) -> None:
    """Emit cleanup completed event."""
    await emit_event(IncrementalEvent(
        event_type=IncrementalEventType.CLEANUP_COMPLETED,
        data={
            "deleted_vectors": deleted_vectors,
            "deleted_chunks": deleted_chunks,
        },
        duration_seconds=duration_seconds,
    ))


class MetricsCollector:
    """Collects metrics from events."""
    
    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics: Dict[str, Any] = {
            "documents_scanned": 0,
            "documents_skipped": 0,
            "documents_updated": 0,
            "documents_deleted": 0,
            "chunks_reused": 0,
            "chunks_regenerated": 0,
            "embeddings_reused": 0,
            "embeddings_regenerated": 0,
            "vectors_deleted": 0,
            "scan_times": [],
            "update_times": [],
            "cleanup_times": [],
        }
    
    def record_event(self, event: IncrementalEvent) -> None:
        """
        Record event metrics.
        
        Args:
            event: Event to record
        """
        if event.event_type == IncrementalEventType.SCAN_COMPLETED:
            self._metrics["documents_scanned"] += 1
            if event.duration_seconds:
                self._metrics["scan_times"].append(event.duration_seconds)
        
        elif event.event_type == IncrementalEventType.DOCUMENT_UNCHANGED:
            self._metrics["documents_skipped"] += 1
        
        elif event.event_type in (
            IncrementalEventType.DOCUMENT_MODIFIED,
            IncrementalEventType.DOCUMENT_NEW,
        ):
            self._metrics["documents_updated"] += 1
        
        elif event.event_type == IncrementalEventType.DOCUMENT_DELETED:
            self._metrics["documents_deleted"] += 1
        
        elif event.event_type == IncrementalEventType.CHUNK_REUSED:
            self._metrics["chunks_reused"] += 1
        
        elif event.event_type == IncrementalEventType.CHUNK_MODIFIED:
            self._metrics["chunks_regenerated"] += 1
        
        elif event.event_type == IncrementalEventType.EMBEDDING_REUSED:
            self._metrics["embeddings_reused"] += 1
        
        elif event.event_type == IncrementalEventType.EMBEDDING_GENERATED:
            self._metrics["embeddings_regenerated"] += 1
        
        elif event.event_type == IncrementalEventType.VECTOR_DELETED:
            self._metrics["vectors_deleted"] += 1
        
        elif event.event_type == IncrementalEventType.SYNC_COMPLETED:
            if event.duration_seconds:
                self._metrics["update_times"].append(event.duration_seconds)
        
        elif event.event_type == IncrementalEventType.CLEANUP_COMPLETED:
            if event.duration_seconds:
                self._metrics["cleanup_times"].append(event.duration_seconds)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.
        
        Returns:
            Metrics dictionary
        """
        import statistics
        
        metrics = self._metrics.copy()
        
        # Calculate averages
        if metrics["scan_times"]:
            metrics["average_scan_time"] = statistics.mean(metrics["scan_times"])
        else:
            metrics["average_scan_time"] = 0.0
        
        if metrics["update_times"]:
            metrics["average_update_time"] = statistics.mean(metrics["update_times"])
        else:
            metrics["average_update_time"] = 0.0
        
        if metrics["cleanup_times"]:
            metrics["average_cleanup_duration"] = statistics.mean(metrics["cleanup_times"])
        else:
            metrics["average_cleanup_duration"] = 0.0
        
        return metrics
    
    def reset(self) -> None:
        """Reset metrics."""
        self._metrics = {
            "documents_scanned": 0,
            "documents_skipped": 0,
            "documents_updated": 0,
            "documents_deleted": 0,
            "chunks_reused": 0,
            "chunks_regenerated": 0,
            "embeddings_reused": 0,
            "embeddings_regenerated": 0,
            "vectors_deleted": 0,
            "scan_times": [],
            "update_times": [],
            "cleanup_times": [],
        }