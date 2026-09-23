"""Incremental re-indexing system for Nebula Search."""

__version__ = "1.0.0"

from app.incremental.config import get_incremental_config
from app.incremental.hashing import (
    calculate_document_hash,
    calculate_metadata_hash,
    calculate_chunk_hash,
    calculate_vector_hash,
    generate_content_fingerprint,
)
from app.incremental.detector import ChangeDetector, DocumentChange, ChangeType
from app.incremental.scanner import DocumentScanner, ScanResult
from app.incremental.diff import ChunkDiff, DocumentDiff, DiffEngine
from app.incremental.synchronizer import IncrementalSynchronizer
from app.incremental.metadata import MetadataSynchronizer
from app.incremental.tracker import IndexTracker, IndexStatus
from app.incremental.cleanup import CleanupService
from app.incremental.scheduler import IncrementalScheduler
from app.incremental.events import IncrementalEventType, IncrementalEvent
from app.incremental.services import IncrementalIndexingService
from app.incremental.routes import router as incremental_router

__all__ = [
    "get_incremental_config",
    "calculate_document_hash",
    "calculate_metadata_hash",
    "calculate_chunk_hash",
    "calculate_vector_hash",
    "generate_content_fingerprint",
    "ChangeDetector",
    "DocumentChange",
    "ChangeType",
    "DocumentScanner",
    "ScanResult",
    "ChunkDiff",
    "DocumentDiff",
    "DiffEngine",
    "IncrementalSynchronizer",
    "MetadataSynchronizer",
    "IndexTracker",
    "IndexStatus",
    "CleanupService",
    "IncrementalScheduler",
    "IncrementalEventType",
    "IncrementalEvent",
    "IncrementalIndexingService",
    "incremental_router",
]