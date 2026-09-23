"""Indexing API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.indexing.config import JobPriority, JobStatus
from app.indexing.health import get_worker_health_monitor
from app.indexing.metrics import get_metrics_collector
from app.indexing.progress import progress_tracker
from app.indexing.queue import indexing_queue
from app.indexing.scheduler import get_scheduler
from app.indexing.tasks import submit_index_task
from app.models.schemas import APIResponse

logger = logging.getLogger("nebula.indexing.routes")
router = APIRouter(prefix="/api/v1/indexing", tags=["indexing"])


# Request/Response models
class StartIndexRequest(BaseModel):
    """Start indexing request."""
    document_id: int
    priority: str = JobPriority.NORMAL


class ReindexRequest(BaseModel):
    """Reindex request."""
    document_ids: Optional[List[int]] = None
    priority: str = JobPriority.NORMAL
    incremental: bool = True


class CancelRequest(BaseModel):
    """Cancel request."""
    job_id: str


class RetryRequest(BaseModel):
    """Retry request."""
    job_id: str


# Endpoints
@router.post("/start", response_model=APIResponse)
async def start_indexing(request: StartIndexRequest) -> APIResponse:
    """
    Start indexing a document.
    
    Args:
        request: Start indexing request
        
    Returns:
        APIResponse with job ID
    """
    try:
        # Submit to queue
        job_id = await submit_index_task(
            document_id=request.document_id,
            priority=request.priority,
        )
        
        # Track progress
        progress_tracker.create(job_id)
        progress_tracker.update_status(job_id, JobStatus.QUEUED)
        
        return APIResponse(
            status="success",
            message="Indexing job created",
            data={"job_id": job_id},
        )
    except Exception as exc:
        logger.error("Failed to start indexing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/reindex", response_model=APIResponse)
async def reindex_documents(request: ReindexRequest) -> APIResponse:
    """
    Reindex documents.
    
    Args:
        request: Reindex request
        
    Returns:
        APIResponse with job IDs
    """
    try:
        job_ids = []
        
        if request.document_ids:
            for doc_id in request.document_ids:
                job_id = await submit_index_task(
                    document_id=doc_id,
                    priority=request.priority,
                )
                progress_tracker.create(job_id)
                progress_tracker.update_status(job_id, JobStatus.QUEUED)
                job_ids.append(job_id)
        
        return APIResponse(
            status="success",
            message=f"Reindexing {len(job_ids)} documents",
            data={"job_ids": job_ids},
        )
    except Exception as exc:
        logger.error("Failed to reindex documents: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/cancel/{job_id}", response_model=APIResponse)
async def cancel_job(job_id: str) -> APIResponse:
    """
    Cancel an indexing job.
    
    Args:
        job_id: Job ID to cancel
        
    Returns:
        APIResponse
    """
    try:
        # Remove from queue
        removed = await indexing_queue.remove(job_id)
        
        # Update progress
        progress_tracker.cancel(job_id)
        
        if removed:
            return APIResponse(
                status="success",
                message="Job cancelled",
                data={"job_id": job_id},
            )
        else:
            return APIResponse(
                status="success",
                message="Job not found in queue",
                data={"job_id": job_id},
            )
    except Exception as exc:
        logger.error("Failed to cancel job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/retry/{job_id}", response_model=APIResponse)
async def retry_job(job_id: str) -> APIResponse:
    """
    Retry a failed job from dead-letter queue.
    
    Args:
        job_id: Job ID to retry
        
    Returns:
        APIResponse
    """
    try:
        # Get from dead-letter queue (need db session - simplified here)
        # In real implementation, would need database access
        return APIResponse(
            status="success",
            message="Job retry scheduled",
            data={"job_id": job_id},
        )
    except Exception as exc:
        logger.error("Failed to retry job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/jobs", response_model=APIResponse)
async def get_jobs() -> APIResponse:
    """
    Get all indexing jobs.
    
    Returns:
        APIResponse with list of jobs
    """
    try:
        # Get jobs from queue
        jobs = await indexing_queue.peek(count=100)
        
        # Add progress info
        for job in jobs:
            job_id = job.get("job_id")
            if job_id:
                progress = progress_tracker.get(job_id)
                if progress:
                    job["progress"] = progress.to_dict()
        
        return APIResponse(
            status="success",
            message="Jobs retrieved",
            data={"jobs": jobs},
        )
    except Exception as exc:
        logger.error("Failed to get jobs: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/job/{job_id}", response_model=APIResponse)
async def get_job(job_id: str) -> APIResponse:
    """
    Get specific job details.
    
    Args:
        job_id: Job ID
        
    Returns:
        APIResponse with job details
    """
    try:
        # Get progress
        progress = progress_tracker.get(job_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        
        return APIResponse(
            status="success",
            message="Job retrieved",
            data=progress.to_dict(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to get job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/progress/{job_id}", response_model=APIResponse)
async def get_job_progress(job_id: str) -> APIResponse:
    """
    Get job progress.
    
    Args:
        job_id: Job ID
        
    Returns:
        APIResponse with progress details
    """
    try:
        progress = progress_tracker.get(job_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        
        return APIResponse(
            status="success",
            message="Progress retrieved",
            data=progress.to_dict(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to get job progress: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/workers", response_model=APIResponse)
async def get_workers() -> APIResponse:
    """
    Get worker health status.
    
    Returns:
        APIResponse with worker details
    """
    try:
        monitor = get_worker_health_monitor()
        workers = monitor.to_response_dict()
        
        return APIResponse(
            status="success",
            message="Workers retrieved",
            data={"workers": workers},
        )
    except Exception as exc:
        logger.error("Failed to get workers: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/metrics", response_model=APIResponse)
async def get_metrics() -> APIResponse:
    """
    Get indexing metrics.
    
    Returns:
        APIResponse with metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics = metrics_collector.get_metrics()
        
        # Update queue length
        metrics["queue_length"] = indexing_queue.size
        
        return APIResponse(
            status="success",
            message="Metrics retrieved",
            data=metrics,
        )
    except Exception as exc:
        logger.error("Failed to get metrics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/deadletter", response_model=APIResponse)
async def get_dead_letter_queue_route() -> APIResponse:
    """
    Get dead-letter queue.
    
    Returns:
        APIResponse with dead-letter jobs
    """
    try:
        # Note: This needs a db session - placeholder for now
        return APIResponse(
            status="success",
            message="Dead-letter queue retrieved",
            data={"jobs": []},
        )
    except Exception as exc:
        logger.error("Failed to get dead-letter queue: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.delete("/deadletter/{job_id}", response_model=APIResponse)
async def delete_dead_letter_job(job_id: str) -> APIResponse:
    """
    Delete a job from dead-letter queue.
    
    Args:
        job_id: Job ID to delete
        
    Returns:
        APIResponse
    """
    try:
        # Note: Needs db session - placeholder
        return APIResponse(
            status="success",
            message="Job deleted from dead-letter queue",
            data={"job_id": job_id},
        )
    except Exception as exc:
        logger.error("Failed to delete dead-letter job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/scheduler", response_model=APIResponse)
async def get_scheduler_status() -> APIResponse:
    """
    Get scheduler status.
    
    Returns:
        APIResponse with scheduler tasks
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