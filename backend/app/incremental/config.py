"""Configuration for incremental re-indexing system."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IncrementalReindexMode(str, Enum):
    """Re-indexing mode for incremental updates."""
    FULL = "full"
    INCREMENTAL = "incremental"
    METADATA_ONLY = "metadata_only"


class DocumentState(str, Enum):
    """Document state enumeration."""
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"
    CORRUPTED = "corrupted"
    SKIPPED = "skipped"


class HashAlgorithm(str, Enum):
    """Hash algorithm enumeration."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


@dataclass
class IncrementalConfig:
    """Configuration for incremental re-indexing."""

    # Core settings
    enabled: bool = field(
        default_factory=lambda: os.getenv("ENABLE_INCREMENTAL_INDEXING", "true").lower() == "true"
    )
    hash_algorithm: HashAlgorithm = field(
        default_factory=lambda: HashAlgorithm(
            os.getenv("HASH_ALGORITHM", "sha256")
        )
    )
    reindex_mode: IncrementalReindexMode = field(
        default_factory=lambda: IncrementalReindexMode(
            os.getenv("REINDEX_MODE", "incremental")
        )
    )

    # Scanning settings
    scan_interval: int = field(
        default_factory=lambda: int(os.getenv("SCAN_INTERVAL", "300"))  # 5 minutes default
    )
    scan_batch_size: int = field(
        default_factory=lambda: int(os.getenv("SCAN_BATCH_SIZE", "100"))
    )
    max_scan_threads: int = field(
        default_factory=lambda: int(os.getenv("MAX_SCAN_THREADS", "4"))
    )

    # File watching
    enable_file_watcher: bool = field(
        default_factory=lambda: os.getenv("ENABLE_FILE_WATCHER", "false").lower() == "true"
    )
    debounce_seconds: int = field(
        default_factory=lambda: int(os.getenv("WATCHER_DEBOUNCE_SECONDS", "30"))
    )

    # Change detection thresholds
    content_hash_diff_threshold: float = field(
        default_factory=lambda: float(os.getenv("CONTENT_HASH_DIFF_THRESHOLD", "0.0"))
    )
    metadata_changed_detection: bool = field(
        default_factory=lambda: os.getenv("METADATA_CHANGED_DETECTION", "true").lower() == "true"
    )

    # Incremental chunk settings
    chunk_comparison_enabled: bool = field(
        default_factory=lambda: os.getenv("CHUNK_COMPARISON_ENABLED", "true").lower() == "true"
    )
    chunk_reuse_enabled: bool = field(
        default_factory=lambda: os.getenv("CHUNK_REUSE_ENABLED", "true").lower() == "true"
    )

    # Cleanup settings
    enable_auto_cleanup: bool = field(
        default_factory=lambda: os.getenv("ENABLE_AUTO_CLEANUP", "true").lower() == "true"
    )
    cleanup_orphaned_vectors: bool = field(
        default_factory=lambda: os.getenv("CLEANUP_ORPHANED_VECTORS", "true").lower() == "true"
    )
    cleanup_orphaned_metadata: bool = field(
        default_factory=lambda: os.getenv("CLEANUP_ORPHANED_METADATA", "true").lower() == "true"
    )

    # Metadata sync
    enable_metadata_sync: bool = field(
        default_factory=lambda: os.getenv("ENABLE_METADATA_SYNC", "true").lower() == "true"
    )
    metadata_fields_to_track: list[str] = field(
        default_factory=lambda: os.getenv(
            "METADATA_FIELDS_TO_TRACK",
            "title,description,author,category,tags,language,permissions,collections"
        ).split(",")
    )

    # Scheduling
    enable_auto_schedule: bool = field(
        default_factory=lambda: os.getenv("ENABLE_AUTO_SCHEDULE", "true").lower() == "true"
    )
    default_cron_schedule: str = field(
        default_factory=lambda: os.getenv("DEFAULT_CRON_SCHEDULE", "0 * * * *")  # Every hour
    )

    # Performance
    max_batch_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_BATCH_SIZE", "1000"))
    )
    worker_concurrency: int = field(
        default_factory=lambda: int(os.getenv("WORKER_CONCURRENCY", "2"))
    )
    max_embedding_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_EMBEDDING_RETRIES", "3"))
    )

    # Detection features
    enable_rename_detection: bool = field(
        default_factory=lambda: os.getenv("ENABLE_RENAME_DETECTION", "true").lower() == "true"
    )
    enable_move_detection: bool = field(
        default_factory=lambda: os.getenv("ENABLE_MOVE_DETECTION", "true").lower() == "true"
    )
    enable_corruption_detection: bool = field(
        default_factory=lambda: os.getenv("ENABLE_CORRUPTION_DETECTION", "true").lower() == "true"
    )

    # Metrics and logging
    enable_detailed_metrics: bool = field(
        default_factory=lambda: os.getenv("ENABLE_DETAILED_METRICS", "true").lower() == "true"
    )
    metrics_retention_days: int = field(
        default_factory=lambda: int(os.getenv("METRICS_RETENTION_DAYS", "30"))
    )

    # Retry and fault tolerance
    max_scan_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_SCAN_RETRIES", "3"))
    )
    scan_retry_delay_seconds: int = field(
        default_factory=lambda: int(os.getenv("SCAN_RETRY_DELAY_SECONDS", "60"))
    )

    @property
    def scan_interval_seconds(self) -> int:
        """Get scan interval in seconds."""
        return self.scan_interval

    def get_hash_algorithm(self) -> str:
        """Get hash algorithm name."""
        return self.hash_algorithm.value

    def is_incremental_mode(self) -> bool:
        """Check if incremental mode is enabled."""
        return self.enabled and self.reindex_mode == IncrementalReindexMode.INCREMENTAL

    def is_full_mode(self) -> bool:
        """Check if full reindex mode is enabled."""
        return self.reindex_mode == IncrementalReindexMode.FULL


@dataclass
class ReindexJobConfig:
    """Configuration for a reindex job."""
    document_id: int
    incremental: bool = True
    priority: str = "NORMAL"
    force_full: bool = False
    scan_only: bool = False
    metadata_only: bool = False
    batch_size: Optional[int] = None


_config: Optional[IncrementalConfig] = None


def get_incremental_config() -> IncrementalConfig:
    """Get global incremental config instance (singleton)."""
    global _config
    if _config is None:
        _config = IncrementalConfig()
    return _config


def set_incremental_config(config: IncrementalConfig) -> None:
    """Set global incremental config instance (for testing)."""
    global _config
    _config = config