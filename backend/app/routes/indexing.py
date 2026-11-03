"""Indexing API routes."""

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.indexing.config import JobPriority, JobStatus
from app.indexing.health import get_worker_health_monitor
from app.indexing.metrics import get_metrics_collector
from app.indexing.progress import progress_tracker
from app.indexing.queue import indexing_queue
from app.indexing.retry import get_retry_handler
from app.indexing.scheduler import get_scheduler
from app.indexing.tasks import submit_index_task
from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.indexing_job import IndexingJobRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import APIResponse, PaginationMeta
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


async def _owned_progress(job_id: str, user_id: int, db):
    record = await IndexingJobRepository(db).get_for_user(job_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    progress = progress_tracker.get(job_id)
    if progress and progress.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    if not progress:
        progress = progress_tracker.create(
            job_id,
            user_id=user_id,
            document_id=record["document_id"],
        )
        progress_tracker.update_status(job_id, record["status"])
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
@router.post("/jobs", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
@router.post("/start", response_model=APIResponse)
async def start_indexing(
    request: StartIndexRequest,
    response: Response,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
) -> APIResponse:
    """
    Start indexing a document.
    
    Args:
        request: Start indexing request
        
    Returns:
        APIResponse with job ID
    """
    try:
        user_id = await _owner_context(db, email, request.document_id)
        job_id = str(uuid.uuid4())
        jobs = IndexingJobRepository(db)
        document = await DocumentRepository(db).get_by_id(request.document_id, user_id)
        await jobs.create(job_id, user_id, request.document_id, document["filename"], request.priority)
        try:
            await submit_index_task(
                document_id=request.document_id,
                user_id=user_id,
                job_id=job_id,
                filename=document["filename"],
                file_path=document["storage_path"],
                priority=request.priority,
            )
        except BaseException:
            await jobs.delete_for_user(job_id, user_id)
            raise
        
        # Track progress
        progress_tracker.create(job_id, user_id=user_id, document_id=request.document_id)
        progress_tracker.update_status(job_id, JobStatus.QUEUED)
        response.headers["Location"] = f"/api/v1/indexing/jobs/{job_id}"
        
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
            # Validate all IDs before creating jobs so a rejected batch has
            # no partial queue side effects.
            documents_repo = DocumentRepository(db)
            documents = []
            for doc_id in request.document_ids:
                document = await documents_repo.get_by_id(doc_id, user_id)
                if document is None:
                    raise HTTPException(status_code=404, detail="Document not found")
                documents.append((doc_id, document))

            for doc_id, document in documents:
                job_id = str(uuid.uuid4())
                jobs = IndexingJobRepository(db)
                await jobs.create(job_id, user_id, doc_id, document["filename"], request.priority)
                try:
                    await submit_index_task(
                        document_id=doc_id,
                        user_id=user_id,
                        job_id=job_id,
                        filename=document["filename"],
                        file_path=document["storage_path"],
                        priority=request.priority,
                    )
                except BaseException:
                    await jobs.delete_for_user(job_id, user_id)
                    raise
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


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse)
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
        progress = await _owned_progress(job_id, user_id, db)
        # Remove from queue
        removed = await indexing_queue.remove(job_id)
        
        # Update progress
        if removed:
            progress_tracker.cancel(job_id)
            await IndexingJobRepository(db).set_status(job_id, JobStatus.CANCELLED)
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


@router.post("/jobs/{job_id}/retry", response_model=APIResponse)
@router.post("/retry/{job_id}", response_model=APIResponse)
async def retry_job(
    job_id: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
) -> APIResponse:
    """
    Retry an eligible failed job owned by the current user.
    
    Args:
        job_id: Job ID to retry
        
    Returns:
        APIResponse
    """
    user_id = await _owner_context(db, email)
    jobs = IndexingJobRepository(db)
    record = await jobs.get_for_user(job_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    if record["status"] != JobStatus.FAILED:
        raise HTTPException(status_code=409, detail="Job is not in a retryable state")

    retry_handler = get_retry_handler()
    retry_count = int(record.get("retry_count") or 0)
    if not retry_handler.should_retry(
        Exception(record.get("error_message") or ""), retry_count
    ):
        raise HTTPException(status_code=409, detail="Job is not eligible for retry")

    document = await DocumentRepository(db).get_by_id(record["document_id"], user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Job not found")

    if not await jobs.reserve_retry_for_user(job_id, user_id, retry_handler.max_retries):
        raise HTTPException(status_code=409, detail="Job is not eligible for retry")

    next_retry_count = retry_count + 1
    try:
        queued_id = await submit_index_task(
            document_id=record["document_id"],
            user_id=user_id,
            job_id=job_id,
            filename=document["filename"],
            file_path=document["storage_path"],
            priority=record.get("priority") or JobPriority.NORMAL,
            retry_count=next_retry_count,
        )
        if queued_id != job_id:
            raise RuntimeError("Queue returned a different job identifier")
    except Exception as exc:
        await jobs.set_status(job_id, JobStatus.FAILED, retry_count=next_retry_count)
        raise HTTPException(
            status_code=503,
            detail="Job retry could not be queued",
        ) from exc

    await jobs.set_status(job_id, JobStatus.QUEUED, retry_count=next_retry_count)
    progress_tracker.create(job_id, user_id=user_id, document_id=record["document_id"])
    progress_tracker.update_status(job_id, JobStatus.QUEUED)
    return APIResponse(
        status="success",
        message="Job retry queued",
        data={"job_id": job_id, "status": JobStatus.QUEUED},
    )


@router.get("/jobs", response_model=APIResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
) -> APIResponse:
    """
    Get all indexing jobs.
    
    Returns:
        APIResponse with list of jobs
    """
    try:
        user_id = await _owner_context(db, email)
        # Query durable job records by owner so completed jobs remain private and visible.
        repository = IndexingJobRepository(db)
        jobs = await repository.list_for_user(
            user_id, limit=page_size, offset=(page - 1) * page_size
        )
        total = await repository.count_for_user(user_id)
        
        # Add progress info
        for job in jobs:
            job_id = job.get("job_id")
            if job_id:
                progress = progress_tracker.get(job_id)
                if progress:
                    job["progress"] = progress.to_dict()
                else:
                    job["progress"] = {
                        "job_id": job_id,
                        "status": job["status"],
                        "progress": job["progress"],
                        "current_step": job["current_step"],
                        "worker_id": job["worker_id"],
                    }
        
        return APIResponse(
            status="success",
            message="Jobs retrieved",
            data={
                "jobs": jobs,
                "pagination": PaginationMeta(
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=(total + page_size - 1) // page_size,
                    has_next=page * page_size < total,
                    has_previous=page > 1,
                ).model_dump(),
            },
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get jobs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve indexing jobs",
        )


@router.get("/jobs/{job_id}", response_model=APIResponse)
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
        progress = await _owned_progress(job_id, user_id, db)
        
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


@router.get("/jobs/{job_id}/progress", response_model=APIResponse)
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
        progress = await _owned_progress(job_id, user_id, db)
        
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
