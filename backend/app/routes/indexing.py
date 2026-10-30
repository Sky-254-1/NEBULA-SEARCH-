"""Indexing API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.indexing.config import JobPriority, JobStatus
from app.indexing.health import get_worker_health_monitor
from app.indexing.metrics import get_metrics_collector
from app.indexing.progress import progress_tracker
from app.indexing.queue import indexing_queue
from app.indexing.scheduler import get_scheduler
from app.indexing.tasks import submit_index_task
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import APIResponse
from app.services.auth import get_current_user, require_admin

logger = logging.getLogger("nebula.indexing.routes")
router = APIRouter(prefix="/api/v1/indexing", tags=["indexing"])


async def _owner_context(db, email: str, document_id: int | None = None) -> int:
    user_id = await UserRepository(db).get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="Resource not found")
    if document_id is not None:
        document = await DocumentRepository(db).get_by_id(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
    return user_id


def _owned_progress(job_id: str, user_id: int):
    progress = progress_tracker.get(job_id)
    if not progress or progress.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return progress


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
async def start_indexing(request: StartIndexRequest, email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Start indexing a document.
    
    Args:
        request: Start indexing request
        
    Returns:
        APIResponse with job ID
    """
    try:
        user_id = await _owner_context(db, email, request.document_id)
        # Submit to queue
        job_id = await submit_index_task(
            document_id=request.document_id,
            user_id=user_id,
            priority=request.priority,
        )
        
        # Track progress
        progress_tracker.create(job_id, user_id=user_id, document_id=request.document_id)
        progress_tracker.update_status(job_id, JobStatus.QUEUED)
        
        return APIResponse(
            status="success",
            message="Indexing job created",
            data={"job_id": job_id},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to start indexing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start indexing job",
        )


@router.post("/reindex", response_model=APIResponse)
async def reindex_documents(request: ReindexRequest, email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Reindex documents.
    
    Args:
        request: Reindex request
        
    Returns:
        APIResponse with job IDs
    """
    try:
        user_id = await _owner_context(db, email)
        job_ids = []
        
        if request.document_ids:
            for doc_id in request.document_ids:
                await _owner_context(db, email, doc_id)
                job_id = await submit_index_task(
                    document_id=doc_id,
                    user_id=user_id,
                    priority=request.priority,
                )
                progress_tracker.create(job_id, user_id=user_id, document_id=doc_id)
                progress_tracker.update_status(job_id, JobStatus.QUEUED)
                job_ids.append(job_id)
        
        return APIResponse(
            status="success",
            message=f"Reindexing {len(job_ids)} documents",
            data={"job_ids": job_ids},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to reindex documents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start reindexing jobs",
        )


@router.post("/cancel/{job_id}", response_model=APIResponse)
async def cancel_job(job_id: str, email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Cancel an indexing job.
    
    Args:
        job_id: Job ID to cancel
        
    Returns:
        APIResponse
    """
    try:
        user_id = await _owner_context(db, email)
        progress = _owned_progress(job_id, user_id)
        # Remove from queue
        removed = await indexing_queue.remove(job_id)
        
        # Update progress
        if removed:
            progress_tracker.cancel(job_id)
        elif progress.status not in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise HTTPException(status_code=409, detail="Job is already being processed")
        
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
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to cancel job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to cancel indexing job",
        )


@router.post("/retry/{job_id}", response_model=APIResponse)
async def retry_job(job_id: str, _admin=Depends(require_admin)) -> APIResponse:
    """
    Retry a failed job from dead-letter queue.
    
    Args:
        job_id: Job ID to retry
        
    Returns:
        APIResponse
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Dead-letter retry is not supported")


@router.get("/jobs", response_model=APIResponse)
async def get_jobs(email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Get all indexing jobs.
    
    Returns:
        APIResponse with list of jobs
    """
    try:
        user_id = await _owner_context(db, email)
        # Get jobs from queue
        jobs = [job for job in await indexing_queue.peek(count=100) if job.get("user_id") == user_id]
        
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
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get jobs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve indexing jobs",
        )


@router.get("/job/{job_id}", response_model=APIResponse)
async def get_job(job_id: str, email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Get specific job details.
    
    Args:
        job_id: Job ID
        
    Returns:
        APIResponse with job details
    """
    try:
        # Get progress
        user_id = await _owner_context(db, email)
        progress = _owned_progress(job_id, user_id)
        
        return APIResponse(
            status="success",
            message="Job retrieved",
            data=progress.to_dict(),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve indexing job",
        )


@router.get("/progress/{job_id}", response_model=APIResponse)
async def get_job_progress(job_id: str, email: str = Depends(get_current_user), db=Depends(get_db)) -> APIResponse:
    """
    Get job progress.
    
    Args:
        job_id: Job ID
        
    Returns:
        APIResponse with progress details
    """
    try:
        user_id = await _owner_context(db, email)
        progress = _owned_progress(job_id, user_id)
        
        return APIResponse(
            status="success",
            message="Progress retrieved",
            data=progress.to_dict(),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get job progress")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve job progress",
        )


@router.get("/workers", response_model=APIResponse)
async def get_workers(_admin=Depends(require_admin)) -> APIResponse:
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
    except Exception:
        logger.exception("Failed to get workers")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve worker status",
        )


@router.get("/metrics", response_model=APIResponse)
async def get_metrics(_admin=Depends(require_admin)) -> APIResponse:
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
    except Exception:
        logger.exception("Failed to get metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve indexing metrics",
        )


@router.get("/deadletter", response_model=APIResponse)
async def get_dead_letter_queue_route(_admin=Depends(require_admin)) -> APIResponse:
    """
    Get dead-letter queue.
    
    Returns:
        APIResponse with dead-letter jobs
    """
    raise HTTPException(status_code=501, detail="Dead-letter queue is not supported")


@router.delete("/deadletter/{job_id}", response_model=APIResponse)
async def delete_dead_letter_job(job_id: str, _admin=Depends(require_admin)) -> APIResponse:
    """
    Delete a job from dead-letter queue.
    
    Args:
        job_id: Job ID to delete
        
    Returns:
        APIResponse
    """
    raise HTTPException(status_code=501, detail="Dead-letter queue is not supported")


@router.get("/scheduler", response_model=APIResponse)
async def get_scheduler_status(_admin=Depends(require_admin)) -> APIResponse:
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
    except Exception:
        logger.exception("Failed to get scheduler status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve scheduler status",
        )
