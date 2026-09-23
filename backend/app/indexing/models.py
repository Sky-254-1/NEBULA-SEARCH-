"""Pydantic models for indexing system."""

from typing import Optional
from pydantic import BaseModel


class IndexJobResponse(BaseModel):
    """Index job response."""
    job_id: str
    document_id: int
    filename: str
    priority: str
    status: str
    progress: int
    current_step: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    worker_id: Optional[str] = None
    retry_count: int
    error_message: Optional[str] = None
    duration: Optional[float] = None
    embedding_count: int = 0
    chunk_count: int = 0
    file_size: Optional[int] = None


class IndexJobProgressResponse(BaseModel):
    """Index job progress response."""
    job_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    eta_seconds: Optional[float] = None
    speed: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    worker_id: Optional[str] = None


class WorkerHealthResponse(BaseModel):
    """Worker health response."""
    worker_id: str
    status: str
    cpu_usage: float
    memory_usage: float
    current_job_id: Optional[str] = None
    processed_jobs: int
    failed_jobs: int
    average_duration: float
    heartbeat: str


class DeadLetterJobResponse(BaseModel):
    """Dead letter job response."""
    id: int
    job_id: str
    document_id: int
    filename: str
    failure_reason: str
    retries: int
    failed_at: str
    worker_id: Optional[str] = None
    stack_trace: Optional[str] = None


class IndexingMetricsResponse(BaseModel):
    """Indexing metrics response."""
    indexed_documents: int
    queue_length: int
    average_indexing_time: float
    worker_utilization: float
    embedding_speed: float
    chunks_indexed: int
    failures: int
    retries: int
    cancelled_jobs: int
    storage_throughput: float


class StartIndexRequest(BaseModel):
    """Start indexing request."""
    document_id: int
    priority: str = "NORMAL"


class ReindexRequest(BaseModel):
    """Reindex request."""
    document_ids: Optional[list[int]] = None
    priority: str = "NORMAL"
    incremental: bool = True


class CancelRequest(BaseModel):
    """Cancel request."""
    job_id: str


class RetryRequest(BaseModel):
    """Retry request."""
    job_id: str