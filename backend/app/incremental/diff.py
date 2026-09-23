"""Chunk and document diff engine for incremental re-indexing."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.incremental.diff")


class DiffOperationType(str, Enum):
    """Type of diff operation."""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    REUSE = "reuse"


@dataclass
class ChunkDiff:
    """Represents a difference in a single chunk."""
    chunk_id: int
    operation: DiffOperationType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_embedding_id: Optional[str] = None
    new_embedding_id: Optional[str] = None
    requires_embedding: bool = False
    position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentDiff:
    """Represents differences in a document."""
    document_id: int
    total_chunks: int
    added_chunks: List[ChunkDiff] = field(default_factory=list)
    removed_chunks: List[ChunkDiff] = field(default_factory=list)
    modified_chunks: List[ChunkDiff] = field(default_factory=list)
    reused_chunks: List[ChunkDiff] = field(default_factory=list)
    metadata_changed: bool = False
    metadata_changes: Dict[str, Any] = field(default_factory=dict)
    requires_full_reindex: bool = False
    estimated_embedding_calls: int = 0
    estimated_vector_updates: int = 0


class DiffEngine:
    """
    Computes differences between document versions.
    
    Determines which chunks need to be added, removed, modified, or reused
    to minimize indexing operations.
    """

    def __init__(self) -> None:
        """Initialize diff engine."""
        pass
    
    def compute_diff(
        self,
        document_id: int,
        old_chunks: List[Dict[str, Any]],
        new_chunks: List[str],
        old_metadata: Dict[str, Any],
        new_metadata: Dict[str, Any],
        chunk_reuse_enabled: bool = True,
    ) -> DocumentDiff:
        """
        Compute diff between old and new document state.
        
        Args:
            document_id: Document identifier
            old_chunks: Previous chunk data from database
            new_chunks: Current chunk text list
            old_metadata: Previous metadata
            new_metadata: Current metadata
            chunk_reuse_enabled: Whether to enable chunk reuse
            
        Returns:
            DocumentDiff with all detected differences
        """
        # Build lookup maps
        old_chunk_map = {c["chunk_id"]: c for c in old_chunks}
        
        # Compute metadata changes
        metadata_changed, metadata_changes = self._diff_metadata(
            old_metadata, new_metadata
        )
        
        # Compute chunk diffs
        added = []
        removed = []
        modified = []
        reused = []
        embedding_calls = 0
        vector_updates = 0
        
        max_chunks = max(len(old_chunks), len(new_chunks))
        
        for idx in range(max_chunks):
            chunk_id = idx
            
            if idx >= len(new_chunks):
                # Chunk was removed
                if idx in old_chunk_map:
                    old_chunk = old_chunk_map[idx]
                    removed.append(ChunkDiff(
                        chunk_id=chunk_id,
                        operation=DiffOperationType.REMOVE,
                        old_content=old_chunk.get("content"),
                        old_hash=old_chunk.get("chunk_hash"),
                        old_embedding_id=old_chunk.get("embedding_id"),
                        position=idx,
                    ))
                continue
            
            if idx >= len(old_chunks):
                # New chunk
                new_content = new_chunks[idx]
                new_hash = self._compute_chunk_hash(new_content, idx)
                added.append(ChunkDiff(
                    chunk_id=chunk_id,
                    operation=DiffOperationType.ADD,
                    new_content=new_content,
                    new_hash=new_hash,
                    requires_embedding=True,
                    position=idx,
                ))
                embedding_calls += 1
                vector_updates += 1
                continue
            
            # Both old and new exist - compare
            old_chunk = old_chunk_map[idx]
            old_content = old_chunk.get("content", "")
            old_hash = old_chunk.get("chunk_hash", "")
            old_embedding_id = old_chunk.get("embedding_id")
            
            new_content = new_chunks[idx]
            new_hash = self._compute_chunk_hash(new_content, idx)
            
            if old_hash == new_hash and chunk_reuse_enabled:
                # Chunk unchanged - reuse
                reused.append(ChunkDiff(
                    chunk_id=chunk_id,
                    operation=DiffOperationType.REUSE,
                    old_content=old_content,
                    new_content=new_content,
                    old_hash=old_hash,
                    new_hash=new_hash,
                    old_embedding_id=old_embedding_id,
                    position=idx,
                    requires_embedding=False,
                ))
            else:
                # Chunk modified
                modified.append(ChunkDiff(
                    chunk_id=chunk_id,
                    operation=DiffOperationType.MODIFY,
                    old_content=old_content,
                    new_content=new_content,
                    old_hash=old_hash,
                    new_hash=new_hash,
                    old_embedding_id=old_embedding_id,
                    requires_embedding=True,
                    position=idx,
                ))
                embedding_calls += 1
                vector_updates += 1
        
        # Determine if full reindex is needed
        requires_full = (
            len(added) > 100 or
            len(removed) > 100 or
            len(modified) > len(old_chunks) * 0.5
        )
        
        logger.info(
            "Diff for document %d: %d added, %d removed, %d modified, %d reused chunks",
            document_id, len(added), len(removed), len(modified), len(reused)
        )
        
        return DocumentDiff(
            document_id=document_id,
            total_chunks=len(new_chunks),
            added_chunks=added,
            removed_chunks=removed,
            modified_chunks=modified,
            reused_chunks=reused,
            metadata_changed=metadata_changed,
            metadata_changes=metadata_changes,
            requires_full_reindex=requires_full,
            estimated_embedding_calls=embedding_calls,
            estimated_vector_updates=vector_updates,
        )
    
    def _diff_metadata(
        self,
        old_metadata: Dict[str, Any],
        new_metadata: Dict[str, Any],
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Compute metadata differences.
        
        Args:
            old_metadata: Previous metadata
            new_metadata: Current metadata
            
        Returns:
            Tuple of (changed, changes_dict)
        """
        changes = {}
        
        # Fields that affect search
        searchable_fields = [
            "title", "description", "author", "category",
            "tags", "language", "permissions", "collections"
        ]
        
        for field in searchable_fields:
            old_value = old_metadata.get(field)
            new_value = new_metadata.get(field)
            
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                }
        
        return bool(changes), changes
    
    @staticmethod
    def _compute_chunk_hash(content: str, chunk_index: int) -> str:
        """
        Compute hash for chunk content.
        
        Args:
            content: Chunk text
            chunk_index: Chunk position
            
        Returns:
            Hex hash string
        """
        import hashlib
        hash_input = f"{chunk_index}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def optimize_diff(self, diff: DocumentDiff) -> DocumentDiff:
        """
        Optimize diff to minimize operations.
        
        Args:
            diff: Original diff
            
        Returns:
            Optimized diff
        """
        # If too many changes, recommend full reindex
        total_changes = (
            len(diff.added_chunks) +
            len(diff.removed_chunks) +
            len(diff.modified_chunks)
        )
        
        if total_changes > diff.total_chunks * 0.5:
            logger.info(
                "Optimizing diff for document %d: recommending full reindex (%d changes)",
                diff.document_id, total_changes
            )
            diff.requires_full_reindex = True
        
        return diff


class ChunkComparator:
    """Compares chunks to detect differences."""

    @staticmethod
    def compare(
        old_chunk: Dict[str, Any],
        new_content: str,
        new_index: int,
    ) -> ChunkDiff:
        """
        Compare old and new chunk.
        
        Args:
            old_chunk: Previous chunk data
            new_content: New chunk content
            new_index: New chunk index
            
        Returns:
            ChunkDiff describing the difference
        """
        old_content = old_chunk.get("content", "")
        old_hash = old_chunk.get("chunk_hash", "")
        old_embedding_id = old_chunk.get("embedding_id")
        
        new_hash = DiffEngine._compute_chunk_hash(new_content, new_index)
        
        if old_hash == new_hash:
            return ChunkDiff(
                chunk_id=new_index,
                operation=DiffOperationType.REUSE,
                old_content=old_content,
                new_content=new_content,
                old_hash=old_hash,
                new_hash=new_hash,
                old_embedding_id=old_embedding_id,
                position=new_index,
                requires_embedding=False,
            )
        else:
            return ChunkDiff(
                chunk_id=new_index,
                operation=DiffOperationType.MODIFY,
                old_content=old_content,
                new_content=new_content,
                old_hash=old_hash,
                new_hash=new_hash,
                old_embedding_id=old_embedding_id,
                requires_embedding=True,
                position=new_index,
            )