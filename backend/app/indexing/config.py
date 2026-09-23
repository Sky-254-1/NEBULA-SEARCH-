"""Configuration for the indexing system."""

from dataclasses import dataclass
from enum import Enum

from app.config import get_settings


class JobPriority(str, Enum):
    """Job priority levels."""
    SYSTEM = "SYSTEM"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class JobStatus(str, Enum):
    """Job lifecycle states."""
    QUEUED = "QUEUED"
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkerStatus(str, Enum):
    """Worker health status."""
    IDLE = "IDLE"
    BUSY = "BUSY"
    DEAD = "DEAD"
    STOPPED = "STOPPED"


class IndexingStep(str, Enum):
    """Steps in the indexing pipeline."""
    UPLOADING = "UPLOADING"
    READING = "READING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    VECTOR_STORAGE = "VECTOR_STORAGE"
    FINALIZING = "FINALIZING"


@dataclass
class IndexingConfig:
    """Configuration for the indexing system."""
    # Queue settings
    max_queue_size: int = 10000
    priority_limit_system: int = 100
    priority_limit_high: int = 50
    priority_limit_normal: int = 25
    priority_limit_low: int = 10

    # Worker settings
    worker_count: int = 2
    worker_heartbeat_interval: int = 30  # seconds
    worker_restart_on_dead: bool = True

    # Retry settings
    max_retries: int = 5
    retry_base_delay: float = 5.0  # seconds
    retry_backoff_multiplier: float = 3.0

    # Progress settings
    progress_update_interval: float = 0.5  # seconds

    # Metrics settings
    metrics_collection_interval: int = 60  # seconds
    metrics_retention_days: int = 30

    # Scheduler settings
    scheduler_interval: int = 3600  # 1 hour
    nightly_reindex_hour: int = 2  # 2 AM
    weekly_optimization_day: int = 0  # Sunday

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # File type support
    supported_extensions: set[str] = None

    def __post_init__(self) -> None:
        if self.supported_extensions is None:
            self.supported_extensions = {
                ".pdf", ".docx", ".txt", ".md",
                ".markdown", ".html", ".csv", ".json",
            }


def get_indexing_config() -> IndexingConfig:
    """Get indexing configuration from environment."""
    settings = get_settings()
    return IndexingConfig(
        max_queue_size=int(settings.indexing_max_queue_size or 10000),
        worker_count=int(settings.indexing_worker_count or 2),
        max_retries=int(settings.indexing_max_retries or 5),
        retry_base_delay=float(settings.indexing_retry_base_delay or 5.0),
        retry_backoff_multiplier=float(
            settings.indexing_retry_backoff_multiplier or 3.0
        ),
        chunk_size=int(settings.indexing_chunk_size or 1000),
        chunk_overlap=int(settings.indexing_chunk_overlap or 200),
    )
