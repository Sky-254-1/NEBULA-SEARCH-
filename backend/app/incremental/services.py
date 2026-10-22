"""Main service for incremental re-indexing."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.incremental.config import (
    IncrementalConfig,
    ReindexJobConfig,
    get_incremental_config,
)
from app.incremental.detector import ChangeDetector, ChangeType
from app.incremental.diff import DiffEngine
from app.incremental.events import (
    emit_change_detected,
    emit_cleanup_completed,
    emit_document_deleted,
    emit_document_modified,
    emit_document_new,
    emit_document_unchanged,
    emit_sync_completed,
    get_event_manager,
)
from app.incremental.metadata import MetadataSynchronizer
from app.incremental.scanner import DocumentScanner
from app.incremental.synchronizer import IncrementalSynchronizer
from app.incremental.tracker import IndexTracker, IndexStatus
from app.incremental.cleanup import CleanupService

logger = logging.getLogger("nebula.incremental.services")


@dataclass
class ReindexJobResult:
    """Result of re-indexing job."""
    document_id: int
    success: bool
    change_type: str
    scan_duration: float = 0.0
    sync_duration: float = 0.0
    total_duration: float = 0.0
    chunks_added: int = 0
    chunks_removed: int = 0
    chunks_modified: int = 0
    chunks_reused: int = 0
    embeddings_generated: int = 0
    embeddings_reused: int = 0
    metadata_updated: bool = False
    error: Optional[str] = None


class IncrementalIndexingService:
    """
    Main service for incremental re-indexing.
    
    Orchestrates scanning, change detection, diffing, synchronization,
    and cleanup operations.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize service."""
        self._config = config or get_incremental_config()
        self._settings = get_settings()
        
        # Initialize components
        self._scanner = DocumentScanner()
        self._detector = ChangeDetector()
        self._diff_engine = DiffEngine()
        self._synchronizer = IncrementalSynchronizer()
        self._metadata_sync = MetadataSynchronizer()
        self._tracker = IndexTracker()
        self._cleanup = CleanupService()
        
        # Event manager
        self._events = get_event_manager()
    
    async def reindex_document(
        self,
        db_session,
        document_id: int,
        job_config: ReindexJobConfig,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunks: Optional[List[str]] = None,
    ) -> ReindexJobResult:
        """
        Reindex a single document.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            job_config: Job configuration
            file_path: Path to document file
            metadata: Document metadata
            chunks: Pre-chunked text (optional)
            
        Returns:
            ReindexJobResult
        """
        start_time = time.time()
        result = ReindexJobResult(
            document_id=document_id,
            success=False,
            change_type="unknown",
        )
        
        try:
            # Get old document state
            old_document = await self._get_document_state(db_session, document_id)
            
            # Step 1: Scan document
            logger.info("Scanning document %d", document_id)
            scan_result = await self._scanner.scan_document(
                document_id=document_id,
                file_path=file_path,
                old_document=old_document,
                metadata=metadata,
            )
            result.scan_duration = time.time() - start_time
            
            # Handle scan results
            if scan_result.status == "not_found":
                # Document deleted
                result.change_type = ChangeType.DELETED
                result.success = True
                result.total_duration = time.time() - start_time
                
                await emit_document_deleted(document_id)
                await self._tracker.update_status(db_session, document_id, IndexStatus.SKIPPED)
                
                return result
            
            if scan_result.status == "error":
                result.error = scan_result.error
                result.total_duration = time.time() - start_time
                return result
            
            if scan_result.change_type == "unchanged":
                # Document unchanged - skip
                result.change_type = ChangeType.UNCHANGED
                result.success = True
                result.total_duration = time.time() - start_time
                
                await emit_document_unchanged(document_id)
                await self._tracker.record_scan(
                    db_session, document_id,
                    scan_result.file_hash,
                    scan_result.metadata_hash,
                    scan_result.last_modified,
                )
                
                return result
            
            # Step 2: Chunk document if needed
            if not chunks and file_path:
                chunks = await self._chunk_document(file_path)
            elif not chunks:
                chunks = []
            
            # Step 3: Detect changes
            logger.info("Detecting changes for document %d", document_id)
            change = await self._detector.detect_changes(
                document_id=document_id,
                file_path=file_path,
                old_document=old_document,
                new_chunks=chunks,
                new_metadata=metadata or {},
            )
            
            result.change_type = change.change_type
            
            # Handle different change types
            if change.change_type == ChangeType.NEW:
                await emit_document_new(document_id)
            
            elif change.change_type == ChangeType.RENAMED:
                # Only update metadata
                await self._metadata_sync.sync_metadata(
                    db_session, document_id,
                    old_document.get("metadata", {}),
                    metadata or {},
                )
                result.metadata_updated = True
                result.success = True
                result.total_duration = time.time() - start_time
                return result
            
            elif change.change_type == ChangeType.MOVED:
                result.success = True
                result.total_duration = time.time() - start_time
                return result
            
            elif change.change_type in (ChangeType.MODIFIED, ChangeType.CORRUPTED):
                await emit_document_modified(document_id)
            
            # Step 4: Compute diff
            old_chunks = old_document.get("chunks", []) if old_document else []
            old_metadata = old_document.get("metadata", {}) if old_document else {}
            
            document_diff = self._diff_engine.compute_diff(
                document_id=document_id,
                old_chunks=old_chunks,
                new_chunks=chunks,
                old_metadata=old_metadata,
                new_metadata=metadata or {},
            )
            
            # Step 5: Synchronize
            logger.info("Synchronizing document %d", document_id)
            sync_start = time.time()
            
            sync_result = await self._synchronizer.synchronize(
                db_session, document_id, document_diff,
                metadata or {}, file_path
            )
            
            result.sync_duration = time.time() - sync_start
            result.chunks_added = sync_result.chunks_added
            result.chunks_removed = sync_result.chunks_removed
            result.chunks_modified = sync_result.chunks_modified
            result.chunks_reused = len(document_diff.reused_chunks)
            result.embeddings_generated = sync_result.chunks_added + sync_result.chunks_modified
            result.embeddings_reused = len(document_diff.reused_chunks)
            result.metadata_updated = sync_result.metadata_updated
            result.success = sync_result.success
            result.error = sync_result.error
            
            # Step 6: Update tracker
            if sync_result.success:
                await self._tracker.increment_version(db_session, document_id)
                
                # Initialize tracking if new document
                if change.change_type == ChangeType.NEW:
                    await self._tracker.initialize_document(
                        db_session, document_id,
                        file_path or "",
                        chunks,
                        metadata=metadata,
                    )
            
            result.total_duration = time.time() - start_time
            
            # Emit events
            await emit_sync_completed(document_id, result.sync_duration)
            await emit_change_detected(
                document_id, change.change_type,
                len(document_diff.added_chunks) + len(document_diff.modified_chunks)
            )
            
            logger.info(
                "Reindexed document %d in %.2fs: %d added, %d removed, %d modified, %d reused",
                document_id, result.total_duration,
                result.chunks_added, result.chunks_removed,
                result.chunks_modified, result.chunks_reused,
            )
            
            return result
            
        except Exception as exc:
            logger.error("Reindex failed for document %d: %s", document_id, exc)
            result.error = str(exc)
            result.total_duration = time.time() - start_time
            return result
    
    async def scan_all(
        self,
        db_session,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Scan all documents for changes.
        
        Args:
            db_session: Database session
            limit: Maximum documents to scan
            
        Returns:
            Scan summary
        """
        logger.info("Starting full scan (limit=%d)", limit)
        start_time = time.time()
        
        try:
            # Get all documents
            cursor = await db_session.execute(
                "SELECT id, storage_path, metadata FROM documents LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            
            documents = []
            for row in rows:
                doc_id, storage_path, metadata_json = row
                documents.append({
                    "id": doc_id,
                    "storage_path": storage_path,
                    "metadata": metadata_json,
                })
            
            # Scan all documents
            scan_results = await self._scanner.scan_batch(documents)
            
            # Process results
            needs_reindex = []
            unchanged = 0
            modified = 0
            new_docs = 0
            deleted = 0
            
            for scan_result in scan_results:
                if scan_result.change_type == "new":
                    new_docs += 1
                    needs_reindex.append(scan_result.document_id)
                elif scan_result.change_type == "modified":
                    modified += 1
                    needs_reindex.append(scan_result.document_id)
                elif scan_result.change_type == "deleted":
                    deleted += 1
                elif scan_result.change_type == "unchanged":
                    unchanged += 1
            
            duration = time.time() - start_time
            
            summary = {
                "total_scanned": len(scan_results),
                "unchanged": unchanged,
                "modified": modified,
                "new": new_docs,
                "deleted": deleted,
                "needs_reindex": needs_reindex,
                "duration_seconds": duration,
            }
            
            logger.info(
                "Scan completed in %.2fs: %d unchanged, %d modified, %d new, %d deleted",
                duration, unchanged, modified, new_docs, deleted
            )
            
            return summary
            
        except Exception as exc:
            logger.error("Full scan failed: %s", exc)
            return {"error": str(exc)}
    
    async def cleanup(
        self,
        db_session,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Run cleanup of stale data.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Cleanup results
        """
        logger.info("Starting cleanup (dry_run=%s)", dry_run)
        
        result = await self._cleanup.cleanup(db_session, dry_run)
        
        if result.success:
            await emit_cleanup_completed(
                result.deleted_vectors,
                result.deleted_chunks,
                result.duration_seconds,
            )
        
        return {
            "success": result.success,
            "deleted_vectors": result.deleted_vectors,
            "deleted_metadata": result.deleted_metadata,
            "deleted_chunks": result.deleted_chunks,
            "deleted_cache": result.deleted_cache,
            "deleted_history": result.deleted_history,
            "duration_seconds": result.duration_seconds,
            "errors": result.errors,
        }
    
    async def get_stats(self, db_session) -> Dict[str, Any]:
        """
        Get incremental indexing statistics.
        
        Args:
            db_session: Database session
            
        Returns:
            Statistics dictionary
        """
        try:
            # Get document counts
            cursor = await db_session.execute("SELECT COUNT(*) FROM documents")
            row = await cursor.fetchone()
            total_documents = row[0] if row else 0
            
            # Get tracking counts
            cursor = await db_session.execute("SELECT COUNT(*) FROM index_tracking")
            row = await cursor.fetchone()
            tracked_documents = row[0] if row else 0
            
            # Get metrics
            cursor = await db_session.execute(
                "SELECT metric_name, COUNT(*) FROM indexing_metrics GROUP BY metric_name"
            )
            metrics_rows = await cursor.fetchall()
            
            # Get event metrics
            event_metrics = self._events.get_metrics()
            
            return {
                "total_documents": total_documents,
                "tracked_documents": tracked_documents,
                "indexing_metrics": dict(metrics_rows),
                "event_metrics": event_metrics,
                "enabled": self._config.enabled,
                "mode": self._config.reindex_mode.value,
            }
            
        except Exception as exc:
            logger.error("Failed to get stats: %s", exc)
            return {"error": str(exc)}
    
    async def _get_document_state(
        self,
        db_session,
        document_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current document state from tracking.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            
        Returns:
            Document state dict or None
        """
        try:
            # Get from index tracker
            record = await self._tracker.get_record(document_id)
            
            if not record:
                # Try to get from database
                cursor = await db_session.execute(
                    """
                    SELECT file_hash, metadata_hash, chunk_hashes, chunk_count,
                           embedding_count, last_modified
                    FROM index_tracking
                    WHERE document_id = ?
                    """,
                    (document_id,),
                )
                row = await cursor.fetchone()
                
                if row:
                    file_hash, metadata_hash, chunk_hashes_str, chunk_count, embedding_count, last_modified = row
                    chunk_hashes = chunk_hashes_str.split(",") if chunk_hashes_str else []
                    
                    return {
                        "file_hash": file_hash,
                        "metadata_hash": metadata_hash,
                        "chunk_hashes": chunk_hashes,
                        "chunk_count": chunk_count,
                        "embedding_count": embedding_count,
                        "last_modified": last_modified,
                    }
            
            return None
            
        except Exception as exc:
            logger.error("Failed to get document state for %d: %s", document_id, exc)
            return None
    
    async def _chunk_document(self, file_path: str) -> List[str]:
        """
        Chunk a document file.
        
        Args:
            file_path: Path to document
            
        Returns:
            List of text chunks
        """
        # Import existing chunking logic
        from app.indexing.tasks import chunk_text
        
        try:
            # Extract text (simplified)
            text = ""
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                # Try binary read for PDFs etc.
                with open(file_path, "rb") as f:
                    text = f.read().decode("utf-8", errors="ignore")
            
            # Chunk text
            chunks = chunk_text(
                text,
                chunk_size=self._settings.indexing_chunk_size,
                chunk_overlap=self._settings.indexing_chunk_overlap,
            )
            
            return chunks
            
        except Exception as exc:
            logger.error("Failed to chunk document %s: %s", file_path, exc)
            return []


def get_incremental_service(config: Optional[IncrementalConfig] = None) -> IncrementalIndexingService:
    """
    Get global incremental service instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        IncrementalIndexingService instance
    """
    if not hasattr(get_incremental_service, "_instance"):
        get_incremental_service._instance = IncrementalIndexingService(config)
    
    return get_incremental_service._instance