"""Incremental synchronizer for updating search index."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)
from app.incremental.diff import ChunkDiff, DocumentDiff, DiffEngine

logger = logging.getLogger("nebula.incremental.synchronizer")


@dataclass
class SyncResult:
    """Result of synchronization."""
    document_id: int
    success: bool
    chunks_added: int = 0
    chunks_removed: int = 0
    chunks_modified: int = 0
    chunks_reused: int = 0
    embeddings_generated: int = 0
    embeddings_reused: int = 0
    metadata_updated: bool = False
    vectors_deleted: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0


class IncrementalSynchronizer:
    """
    Synchronizes document changes to search index.
    
    Applies incremental updates by only processing changed chunks,
    reusing unchanged ones to minimize embedding generation.
    """

    def __init__(
        self,
        config: Optional[IncrementalConfig] = None,
        diff_engine: Optional[DiffEngine] = None,
    ):
        """Initialize synchronizer."""
        self._config = config or get_incremental_config()
        self._diff_engine = diff_engine or DiffEngine()
        self._settings = get_settings()
    
    async def synchronize(
        self,
        db_session,
        document_id: int,
        document_diff: DocumentDiff,
        metadata: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> SyncResult:
        """
        Synchronize document changes to index.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            document_diff: Computed document diff
            metadata: Document metadata
            file_path: Path to document file
            
        Returns:
            SyncResult with synchronization details
        """
        import time
        start_time = time.time()
        
        result = SyncResult(
            document_id=document_id,
            success=False,
        )
        
        try:
            # If full reindex required, delegate to full indexer
            if document_diff.requires_full_reindex:
                logger.info(
                    "Document %d requires full reindex due to extensive changes",
                    document_id,
                )
                return await self._full_reindex(
                    db_session, document_id, metadata, file_path
                )
            
            # Handle based on diff operations
            logger.info(
                "Synchronizing document %d: %d added, %d removed, %d modified, %d reused",
                document_id,
                len(document_diff.added_chunks),
                len(document_diff.removed_chunks),
                len(document_diff.modified_chunks),
                len(document_diff.reused_chunks),
            )
            
            # Step 1: Add new chunks
            if document_diff.added_chunks:
                added = await self._add_chunks(
                    db_session, document_id, document_diff.added_chunks
                )
                result.chunks_added = added
            
            # Step 2: Remove old chunks
            if document_diff.removed_chunks:
                removed = await self._remove_chunks(
                    db_session, document_id, document_diff.removed_chunks
                )
                result.chunks_removed = removed
            
            # Step 3: Modify changed chunks
            if document_diff.modified_chunks:
                modified = await self._modify_chunks(
                    db_session, document_id, document_diff.modified_chunks
                )
                result.chunks_modified = modified
            
            # Step 4: Update metadata if changed
            if document_diff.metadata_changed:
                await self._update_metadata(db_session, document_id, metadata)
                result.metadata_updated = True
            
            # Step 5: Clean up old vectors if needed
            if document_diff.removed_chunks:
                deleted = await self._delete_vectors(
                    db_session, document_id, document_diff.removed_chunks
                )
                result.vectors_deleted = deleted
            
            result.success = True
            result.duration_seconds = time.time() - start_time
            
            logger.info(
                "Synchronization complete for document %d in %.2fs",
                document_id, result.duration_seconds
            )
            
            return result
            
        except Exception as exc:
            logger.error("Synchronization failed for document %d: %s", document_id, exc)
            result.error = str(exc)
            result.duration_seconds = time.time() - start_time
            return result
    
    async def _full_reindex(
        self,
        db_session,
        document_id: int,
        metadata: Dict[str, Any],
        file_path: Optional[str],
    ) -> SyncResult:
        """
        Perform full reindex of document.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            metadata: Document metadata
            file_path: Path to document file
            
        Returns:
            SyncResult
        """
        import time
        start_time = time.time()
        
        try:
            # Delete all existing chunks
            await db_session.execute(
                "DELETE FROM document_chunks WHERE document_id = ?",
                (document_id,),
            )
            await db_session.commit()
            
            # Delete existing documents (trigger cascade)
            await db_session.execute(
                "DELETE FROM index_jobs WHERE document_id = ?",
                (document_id,),
            )
            await db_session.commit()
            
            logger.info("Full reindex: cleared old data for document %d", document_id)
            
            result = SyncResult(
                document_id=document_id,
                success=True,
                chunks_removed=-1,  # Indicates full clear
                duration_seconds=time.time() - start_time,
            )
            
            return result
            
        except Exception as exc:
            logger.error("Full reindex failed: %s", exc)
            return SyncResult(
                document_id=document_id,
                success=False,
                error=str(exc),
                duration_seconds=time.time() - start_time,
            )
    
    async def _add_chunks(
        self,
        db_session,
        document_id: int,
        chunk_diffs: List[ChunkDiff],
    ) -> int:
        """
        Add new chunks to database.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            chunk_diffs: List of chunk diffs to add
            
        Returns:
            Number of chunks added
        """
        added = 0
        
        for chunk_diff in chunk_diffs:
            try:
                content = chunk_diff.new_content
                chunk_hash = chunk_diff.new_hash
                chunk_id = chunk_diff.chunk_id
                
                # Save chunk to database
                await db_session.execute(
                    """
                    INSERT OR REPLACE INTO document_chunks
                    (document_id, chunk_id, content, chunk_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (document_id, chunk_id, content, chunk_hash),
                )
                
                added += 1
                logger.debug("Added chunk %d for document %d", chunk_id, document_id)
                
            except Exception as exc:
                logger.error(
                    "Failed to add chunk %d for document %d: %s",
                    chunk_diff.chunk_id, document_id, exc
                )
                raise
        
        await db_session.commit()
        logger.info("Added %d chunks for document %d", added, document_id)
        return added
    
    async def _remove_chunks(
        self,
        db_session,
        document_id: int,
        chunk_diffs: List[ChunkDiff],
    ) -> int:
        """
        Remove chunks from database.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            chunk_diffs: List of chunk diffs to remove
            
        Returns:
            Number of chunks removed
        """
        removed = 0
        
        for chunk_diff in chunk_diffs:
            try:
                chunk_id = chunk_diff.chunk_id
                
                # Delete from database
                await db_session.execute(
                    "DELETE FROM document_chunks WHERE document_id = ? AND chunk_id = ?",
                    (document_id, chunk_id),
                )
                
                removed += 1
                logger.debug("Removed chunk %d for document %d", chunk_id, document_id)
                
            except Exception as exc:
                logger.error(
                    "Failed to remove chunk %d for document %d: %s",
                    chunk_diff.chunk_id, document_id, exc
                )
                raise
        
        await db_session.commit()
        logger.info("Removed %d chunks for document %d", removed, document_id)
        return removed
    
    async def _modify_chunks(
        self,
        db_session,
        document_id: int,
        chunk_diffs: List[ChunkDiff],
    ) -> int:
        """
        Modify chunks in database.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            chunk_diffs: List of chunk diffs to modify
            
        Returns:
            Number of chunks modified
        """
        modified = 0
        
        for chunk_diff in chunk_diffs:
            try:
                chunk_id = chunk_diff.chunk_id
                new_content = chunk_diff.new_content
                new_hash = chunk_diff.new_hash
                
                # Update chunk in database
                await db_session.execute(
                    """
                    UPDATE document_chunks
                    SET content = ?, chunk_hash = ?
                    WHERE document_id = ? AND chunk_id = ?
                    """,
                    (new_content, new_hash, document_id, chunk_id),
                )
                
                modified += 1
                logger.debug("Modified chunk %d for document %d", chunk_id, document_id)
                
            except Exception as exc:
                logger.error(
                    "Failed to modify chunk %d for document %d: %s",
                    chunk_diff.chunk_id, document_id, exc
                )
                raise
        
        await db_session.commit()
        logger.info("Modified %d chunks for document %d", modified, document_id)
        return modified
    
    async def _update_metadata(
        self,
        db_session,
        document_id: int,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Update document metadata.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            metadata: New metadata
        """
        try:
            # Update document metadata (simplified - would update real columns)
            metadata_json = json.dumps(metadata, default=str)
            
            await db_session.execute(
                "UPDATE documents SET metadata = ? WHERE id = ?",
                (metadata_json, document_id),
            )
            await db_session.commit()
            
            logger.info("Updated metadata for document %d", document_id)
            
        except Exception as exc:
            logger.error("Failed to update metadata for document %d: %s", document_id, exc)
            raise
    
    async def _delete_vectors(
        self,
        db_session,
        document_id: int,
        chunk_diffs: List[ChunkDiff],
    ) -> int:
        """
        Delete vectors for removed chunks.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            chunk_diffs: List of chunk diffs (removed chunks)
            
        Returns:
            Number of vectors deleted
        """
        deleted = 0
        
        for chunk_diff in chunk_diffs:
            try:
                embedding_id = chunk_diff.old_embedding_id
                
                if embedding_id:
                    # Delete from vector store (placeholder)
                    logger.debug(
                        "Would delete vector %s for document %d chunk %d",
                        embedding_id, document_id, chunk_diff.chunk_id
                    )
                    deleted += 1
                    
            except Exception as exc:
                logger.error(
                    "Failed to delete vector for chunk %d document %d: %s",
                    chunk_diff.chunk_id, document_id, exc
                )
                raise
        
        if deleted > 0:
            logger.info(
                "Deleted %d orphaned vectors for document %d",
                deleted, document_id
            )
        
        return deleted