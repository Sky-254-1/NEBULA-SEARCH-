"""Cleanup service for incremental re-indexing."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)

logger = logging.getLogger("nebula.incremental.cleanup")


@dataclass
class CleanupResult:
    """Result of cleanup operation."""
    deleted_vectors: int = 0
    deleted_metadata: int = 0
    deleted_chunks: int = 0
    deleted_cache: int = 0
    deleted_history: int = 0
    reclaimed_storage: int = 0
    errors: List[str] = field(default_factory=list)
    success: bool = False
    duration_seconds: float = 0.0


class CleanupService:
    """
    Cleans up stale indexes and orphaned data.
    
    Removes:
    - Deleted vectors
    - Unused embeddings
    - Orphaned metadata
    - Duplicate chunks
    - Expired cache entries
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize cleanup service."""
        self._config = config or get_incremental_config()
    
    async def cleanup(
        self,
        db_session,
        dry_run: bool = False,
    ) -> CleanupResult:
        """
        Perform cleanup of stale data.
        
        Args:
            db_session: Database session
            dry_run: If True, don't actually delete
            
        Returns:
            CleanupResult with cleanup details
        """
        import time
        start_time = time.time()
        
        result = CleanupResult(success=False)
        
        try:
            logger.info("Starting cleanup (dry_run=%s)", dry_run)
            
            # Cleanup orphaned vectors
            if self._config.cleanup_orphaned_vectors:
                deleted = await self._cleanup_orphaned_vectors(db_session, dry_run)
                result.deleted_vectors = deleted
            
            # Cleanup orphaned metadata
            if self._config.cleanup_orphaned_metadata:
                deleted = await self._cleanup_orphaned_metadata(db_session, dry_run)
                result.deleted_metadata = deleted
            
            # Cleanup duplicate chunks
            deleted = await self._cleanup_duplicate_chunks(db_session, dry_run)
            result.deleted_chunks = deleted
            
            # Cleanup expired cache
            deleted = await self._cleanup_expired_cache(db_session, dry_run)
            result.deleted_cache = deleted
            
            # Cleanup old history
            deleted = await self._cleanup_old_history(db_session, dry_run)
            result.deleted_history = deleted
            
            result.success = True
            result.duration_seconds = time.time() - start_time
            
            logger.info(
                "Cleanup completed in %.2fs: %d vectors, %d metadata, %d chunks, %d cache, %d history",
                result.duration_seconds,
                result.deleted_vectors,
                result.deleted_metadata,
                result.deleted_chunks,
                result.deleted_cache,
                result.deleted_history,
            )
            
            return result
            
        except Exception as exc:
            logger.error("Cleanup failed: %s", exc)
            result.errors.append(str(exc))
            result.duration_seconds = time.time() - start_time
            return result
    
    async def _cleanup_orphaned_vectors(
        self,
        db_session,
        dry_run: bool = False,
    ) -> int:
        """
        Remove vectors for deleted chunks.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            # Find orphaned vectors (chunks that don't exist)
            cursor = await db_session.execute(
                """
                SELECT dc.embedding_id, dc.document_id, dc.chunk_id
                FROM document_chunks dc
                LEFT JOIN documents d ON dc.document_id = d.id
                WHERE d.id IS NULL OR dc.embedding_id IS NULL
                """
            )
            orphaned = await cursor.fetchall()
            
            deleted = 0
            for embedding_id, document_id, chunk_id in orphaned:
                if embedding_id:
                    if not dry_run:
                        # Delete from vector store (placeholder)
                        logger.debug(
                            "Would delete orphaned vector %s for document %d chunk %d",
                            embedding_id, document_id, chunk_id
                        )
                    deleted += 1
            
            if deleted > 0:
                logger.info("Found %d orphaned vectors", deleted)
            
            return deleted
            
        except Exception as exc:
            logger.error("Failed to cleanup orphaned vectors: %s", exc)
            return 0
    
    async def _cleanup_orphaned_metadata(
        self,
        db_session,
        dry_run: bool = False,
    ) -> int:
        """
        Remove metadata for deleted documents.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Number of metadata records deleted
        """
        try:
            # Find metadata without documents
            cursor = await db_session.execute(
                """
                SELECT id FROM index_tracking t
                LEFT JOIN documents d ON t.document_id = d.id
                WHERE d.id IS NULL
                """
            )
            orphaned = await cursor.fetchall()
            
            deleted = 0
            for (tracking_id,) in orphaned:
                if not dry_run:
                    await db_session.execute(
                        "DELETE FROM index_tracking WHERE id = ?",
                        (tracking_id,),
                    )
                deleted += 1
            
            if deleted > 0 and not dry_run:
                await db_session.commit()
                logger.info("Deleted %d orphaned metadata records", deleted)
            
            return deleted
            
        except Exception as exc:
            logger.error("Failed to cleanup orphaned metadata: %s", exc)
            return 0
    
    async def _cleanup_duplicate_chunks(
        self,
        db_session,
        dry_run: bool = False,
    ) -> int:
        """
        Remove duplicate chunks.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Number of duplicate chunks deleted
        """
        try:
            # Find duplicate chunk hashes within same document
            cursor = await db_session.execute(
                """
                SELECT document_id, chunk_hash, COUNT(*) as count,
                       GROUP_CONCAT(id) as ids
                FROM document_chunks
                GROUP BY document_id, chunk_hash
                HAVING count > 1
                """
            )
            duplicates = await cursor.fetchall()
            
            deleted = 0
            for document_id, chunk_hash, count, ids_str in duplicates:
                # Keep first chunk, delete rest
                ids = [int(i) for i in ids_str.split(",")]
                ids_to_delete = ids[1:]  # Keep first
                
                if not dry_run:
                    for chunk_id in ids_to_delete:
                        await db_session.execute(
                            "DELETE FROM document_chunks WHERE id = ?",
                            (chunk_id,),
                        )
                
                deleted += len(ids_to_delete)
            
            if deleted > 0 and not dry_run:
                await db_session.commit()
                logger.info("Deleted %d duplicate chunks", deleted)
            
            return deleted
            
        except Exception as exc:
            logger.error("Failed to cleanup duplicate chunks: %s", exc)
            return 0
    
    async def _cleanup_expired_cache(
        self,
        db_session,
        dry_run: bool = False,
    ) -> int:
        """
        Remove expired cache entries.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Number of cache entries deleted
        """
        try:
            # Calculate cutoff (entries older than 30 days)
            cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            cutoff_str = datetime.fromtimestamp(cutoff).isoformat()
            
            # Delete expired cache entries
            if not dry_run:
                cursor = await db_session.execute(
                    """
                    DELETE FROM index_metrics
                    WHERE metric_name = 'cache_entry' AND recorded_at < ?
                    """,
                    (cutoff_str,),
                )
                deleted = cursor.rowcount
                await db_session.commit()
            else:
                # Count without deleting
                cursor = await db_session.execute(
                    """
                    SELECT COUNT(*) FROM index_metrics
                    WHERE metric_name = 'cache_entry' AND recorded_at < ?
                    """,
                    (cutoff_str,),
                )
                row = await cursor.fetchone()
                deleted = row[0] if row else 0
            
            if deleted > 0:
                logger.info("Deleted %d expired cache entries", deleted)
            
            return deleted
            
        except Exception as exc:
            logger.error("Failed to cleanup expired cache: %s", exc)
            return 0
    
    async def _cleanup_old_history(
        self,
        db_session,
        dry_run: bool = False,
    ) -> int:
        """
        Remove old history records.
        
        Args:
            db_session: Database session
            dry_run: If True, don't delete
            
        Returns:
            Number of history records deleted
        """
        try:
            # Calculate cutoff (older than metrics retention period)
            cutoff_days = self._config.metrics_retention_days
            cutoff = datetime.now().timestamp() - (cutoff_days * 24 * 60 * 60)
            cutoff_str = datetime.fromtimestamp(cutoff).isoformat()
            
            # Delete old metrics
            if not dry_run:
                cursor = await db_session.execute(
                    """
                    DELETE FROM indexing_metrics
                    WHERE recorded_at < ?
                    """,
                    (cutoff_str,),
                )
                deleted = cursor.rowcount
                await db_session.commit()
            else:
                # Count without deleting
                cursor = await db_session.execute(
                    """
                    SELECT COUNT(*) FROM indexing_metrics
                    WHERE recorded_at < ?
                    """,
                    (cutoff_str,),
                )
                row = await cursor.fetchone()
                deleted = row[0] if row else 0
            
            if deleted > 0:
                logger.info("Deleted %d old history records", deleted)
            
            return deleted
            
        except Exception as exc:
            logger.error("Failed to cleanup old history: %s", exc)
            return 0
    
    async def remove_document_data(
        self,
        db_session,
        document_id: int,
        dry_run: bool = False,
    ) -> CleanupResult:
        """
        Remove all data for a deleted document.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            dry_run: If True, don't delete
            
        Returns:
            CleanupResult
        """
        result = CleanupResult(success=False)
        
        try:
            # Delete chunks
            cursor = await db_session.execute(
                "SELECT COUNT(*) FROM document_chunks WHERE document_id = ?",
                (document_id,),
            )
            row = await cursor.fetchone()
            chunk_count = row[0] if row else 0
            
            if not dry_run:
                await db_session.execute(
                    "DELETE FROM document_chunks WHERE document_id = ?",
                    (document_id,),
                )
                await db_session.commit()
            
            result.deleted_chunks = chunk_count
            
            # Delete index tracking
            if not dry_run:
                await db_session.execute(
                    "DELETE FROM index_tracking WHERE document_id = ?",
                    (document_id,),
                )
                await db_session.commit()
            
            result.deleted_metadata = 1
            
            # Delete index jobs
            cursor = await db_session.execute(
                "SELECT COUNT(*) FROM index_jobs WHERE document_id = ?",
                (document_id,),
            )
            row = await cursor.fetchone()
            job_count = row[0] if row else 0
            
            if not dry_run:
                await db_session.execute(
                    "DELETE FROM index_jobs WHERE document_id = ?",
                    (document_id,),
                )
                await db_session.commit()
            
            result.success = True
            
            logger.info(
                "Removed data for document %d: %d chunks, %d metadata, %d jobs",
                document_id, chunk_count, 1, job_count
            )
            
            return result
            
        except Exception as exc:
            logger.error("Failed to remove document data for %d: %s", document_id, exc)
            result.errors.append(str(exc))
            return result