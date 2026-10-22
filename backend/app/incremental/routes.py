"""API routes for incremental re-indexing."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.incremental.config import (
    ReindexJobConfig,
    get_incremental_config,
)
from app.incremental.events import get_event_manager
from app.incremental.scheduler import get_scheduler
from app.incremental.services import get_incremental_service
from app.models.schemas import APIResponse

logger = logging.getLogger("nebula.incremental.routes")
router = APIRouter(prefix="/api/v1/reindex", tags=["reindex"])


# Request/Response models
class ReindexDocumentRequest(BaseModel):
    """Reindex single document request."""
    incremental: bool = True
    force_full: bool = False
    scan_only: bool = False
    metadata_only: bool = False


class ReindexAllRequest(BaseModel):
    """Reindex all documents request."""
    incremental: bool = True
    batch_size: int = 100
    limit: Optional[int] = None


class CleanupRequest(BaseModel):
    """Cleanup request."""
    dry_run: bool = False


class SyncRequest(BaseModel):
    """Sync request."""
    full_scan: bool = False


# Endpoints
@router.get("/status", response_model=APIResponse)
async def get_reindex_status() -> APIResponse:
    """
    Get incremental re-indexing status.
    
    Returns:
        APIResponse with status
    """
    try:
        config = get_incremental_config()
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        
        stats = {}
        if db_session:
            stats = await service.get_stats(db_session)
        
        return APIResponse(
            status="success",
            message="Re-indexing status retrieved",
            data={
                "enabled": config.enabled,
                "mode": config.reindex_mode.value,
                "scan_interval": config.scan_interval,
                "file_watcher": config.enable_file_watcher,
                "stats": stats,
            },
        )
    except Exception as exc:
        logger.error("Failed to get reindex status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/stats", response_model=APIResponse)
async def get_reindex_stats() -> APIResponse:
    """
    Get re-indexing statistics.
    
    Returns:
        APIResponse with stats
    """
    try:
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        stats = {}
        
        if db_session:
            stats = await service.get_stats(db_session)
        
        # Get event metrics
        event_manager = get_event_manager()
        metrics = event_manager.get_metrics()
        
        return APIResponse(
            status="success",
            message="Stats retrieved",
            data={
                "stats": stats,
                "metrics": metrics,
            },
        )
    except Exception as exc:
        logger.error("Failed to get stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/history", response_model=APIResponse)
async def get_reindex_history(limit: int = 100) -> APIResponse:
    """
    Get re-indexing history.
    
    Args:
        limit: Maximum events to return
        
    Returns:
        APIResponse with history
    """
    try:
        event_manager = get_event_manager()
        history = event_manager.get_history(limit=limit)
        
        # Convert to serializable format
        events = [
            {
                "event_type": event.event_type.value,
                "document_id": event.document_id,
                "chunk_id": event.chunk_id,
                "data": event.data,
                "timestamp": event.timestamp,
                "duration_seconds": event.duration_seconds,
                "error": event.error,
            }
            for event in history
        ]
        
        return APIResponse(
            status="success",
            message="History retrieved",
            data={"events": events, "count": len(events)},
        )
    except Exception as exc:
        logger.error("Failed to get history: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/document/{document_id}", response_model=APIResponse)
async def reindex_document(
    document_id: int,
    request: ReindexDocumentRequest,
) -> APIResponse:
    """
    Reindex a specific document.
    
    Args:
        document_id: Document identifier
        request: Reindex request
        
    Returns:
        APIResponse with job result
    """
    try:
        service = get_incremental_service()
        
        # Create job config
        job_config = ReindexJobConfig(
            document_id=document_id,
            incremental=request.incremental and not request.force_full,
            force_full=request.force_full,
            scan_only=request.scan_only,
            metadata_only=request.metadata_only,
        )
        
        # Placeholder for db session and file path
        db_session = None
        file_path = None
        metadata = {}
        
        # Run reindex
        result = await service.reindex_document(
            db_session=db_session,
            document_id=document_id,
            job_config=job_config,
            file_path=file_path,
            metadata=metadata,
        )
        
        return APIResponse(
            status="success" if result.success else "error",
            message=f"Reindex {'completed' if result.success else 'failed'}",
            data={
                "document_id": result.document_id,
                "success": result.success,
                "change_type": result.change_type,
                "chunks_added": result.chunks_added,
                "chunks_removed": result.chunks_removed,
                "chunks_modified": result.chunks_modified,
                "chunks_reused": result.chunks_reused,
                "embeddings_generated": result.embeddings_generated,
                "embeddings_reused": result.embeddings_reused,
                "metadata_updated": result.metadata_updated,
                "total_duration": result.total_duration,
                "error": result.error,
            },
        )
    except Exception as exc:
        logger.error("Failed to reindex document %d: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/all", response_model=APIResponse)
async def reindex_all(request: ReindexAllRequest) -> APIResponse:
    """
    Reindex all documents.
    
    Args:
        request: Reindex all request
        
    Returns:
        APIResponse with summary
    """
    try:
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        
        # Run scan
        summary = await service.scan_all(
            db_session=db_session,
            limit=request.limit or request.batch_size,
        )
        
        return APIResponse(
            status="success",
            message="Full reindex scan completed",
            data=summary,
        )
    except Exception as exc:
        logger.error("Failed to reindex all: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/scan", response_model=APIResponse)
async def scan_documents() -> APIResponse:
    """
    Scan documents for changes.
    
    Returns:
        APIResponse with scan results
    """
    try:
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        
        summary = await service.scan_all(db_session=db_session)
        
        return APIResponse(
            status="success",
            message="Scan completed",
            data=summary,
        )
    except Exception as exc:
        logger.error("Failed to scan documents: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/cleanup", response_model=APIResponse)
async def run_cleanup(request: CleanupRequest) -> APIResponse:
    """
    Run cleanup of stale data.
    
    Args:
        request: Cleanup request
        
    Returns:
        APIResponse with cleanup results
    """
    try:
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        
        result = await service.cleanup(db_session=db_session, dry_run=request.dry_run)
        
        return APIResponse(
            status="success",
            message="Cleanup completed",
            data=result,
        )
    except Exception as exc:
        logger.error("Failed to run cleanup: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/sync", response_model=APIResponse)
async def sync_indexes(request: SyncRequest) -> APIResponse:
    """
    Synchronize indexes with database.
    
    Args:
        request: Sync request
        
    Returns:
        APIResponse with sync results
    """
    try:
        service = get_incremental_service()
        
        # Placeholder for db session
        db_session = None
        
        if request.full_scan:
            result = await service.scan_all(db_session=db_session)
        else:
            result = {"message": "Quick sync completed"}
        
        return APIResponse(
            status="success",
            message="Sync completed",
            data=result,
        )
    except Exception as exc:
        logger.error("Failed to sync indexes: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.delete("/cache", response_model=APIResponse)
async def clear_cache() -> APIResponse:
    """
    Clear re-indexing cache.
    
    Returns:
        APIResponse
    """
    try:
        # Clear event manager history
        event_manager = get_event_manager()
        event_manager.clear_history()
        
        return APIResponse(
            status="success",
            message="Cache cleared",
            data={},
        )
    except Exception as exc:
        logger.error("Failed to clear cache: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/scheduler", response_model=APIResponse)
async def get_scheduler_status() -> APIResponse:
    """
    Get scheduler status.
    
    Returns:
        APIResponse with scheduler status
    """
    try:
        scheduler = get_scheduler()
        tasks = scheduler.get_all_tasks()
        
        return APIResponse(
            status="success",
            message="Scheduler status retrieved",
            data={"tasks": tasks},
        )
    except Exception as exc:
        logger.error("Failed to get scheduler status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/scheduler/run/{task_id}", response_model=APIResponse)
async def run_scheduler_task(task_id: str) -> APIResponse:
    """
    Run scheduler task immediately.
    
    Args:
        task_id: Task identifier
        
    Returns:
        APIResponse
    """
    try:
        scheduler = get_scheduler()
        triggered = await scheduler.run_now(task_id)
        
        if triggered:
            return APIResponse(
                status="success",
                message=f"Task {task_id} triggered",
                data={"task_id": task_id},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to run scheduler task: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )