"""Change detection for incremental re-indexing."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)
from app.incremental.hashing import (
    calculate_chunk_hash,
    calculate_metadata_hash,
    compare_hashes,
)

logger = logging.getLogger("nebula.incremental.detector")


class ChangeType(str, Enum):
    """Type of change detected."""
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"
    CORRUPTED = "corrupted"
    SKIPPED = "skipped"


@dataclass
class DocumentChange:
    """Represents a detected change in a document."""
    document_id: int
    change_type: ChangeType
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    changed_chunks: List[int] = field(default_factory=list)
    unchanged_chunks: List[int] = field(default_factory=list)
    new_chunks: List[int] = field(default_factory=list)
    removed_chunks: List[int] = field(default_factory=list)
    changed_metadata: Dict[str, Any] = field(default_factory=dict)
    metadata_changed: bool = False
    requires_vector_regeneration: bool = False
    requires_full_reindex: bool = False
    reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())


class ChangeDetector:
    """
    Detects changes in documents for incremental re-indexing.
    
    Compares document state (content, metadata, chunks, vectors) to determine
    what needs to be re-indexed.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize change detector."""
        self._config = config or get_incremental_config()
    
    async def detect_changes(
        self,
        document_id: int,
        file_path: Optional[str] = None,
        old_document: Optional[Dict[str, Any]] = None,
        new_chunks: Optional[List[str]] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentChange:
        """
        Detect changes in a document.
        
        Args:
            document_id: Document identifier
            file_path: Path to document file
            old_document: Previous document state (from database)
            new_chunks: Current text chunks
            new_metadata: Current document metadata
            
        Returns:
            DocumentChange describing what changed
        """
        # Case 1: Document doesn't exist - it's new
        if not old_document:
            logger.info("Document %d is new", document_id)
            return DocumentChange(
                document_id=document_id,
                change_type=ChangeType.NEW,
                new_state=new_metadata or {},
            )
        
        # Case 2: File path provided but file doesn't exist - deleted
        if file_path and not Path(file_path).exists():
            logger.info("Document %d file not found: %s", document_id, file_path)
            return DocumentChange(
                document_id=document_id,
                change_type=ChangeType.DELETED,
                old_state=old_document,
                reason=f"File not found: {file_path}",
            )
        
        # Case 3: Check for file corruption
        if file_path and self._config.enable_corruption_detection:
            corrupted = await self._check_corruption(file_path, old_document)
            if corrupted:
                return DocumentChange(
                    document_id=document_id,
                    change_type=ChangeType.CORRUPTED,
                    old_state=old_document,
                    reason="File corruption detected",
                )
        
        # Case 4: Detect rename or move (if enabled)
        if old_document.get("storage_path") and file_path:
            rename_detected = self._detect_rename(
                old_document.get("storage_path", ""),
                file_path,
                old_document.get("file_hash", ""),
            )
            if rename_detected:
                logger.info("Document %d renamed: %s -> %s", document_id, 
                           old_document.get("storage_path"), file_path)
                return DocumentChange(
                    document_id=document_id,
                    change_type=ChangeType.RENAMED,
                    old_state=old_document,
                    new_state={"storage_path": file_path, **(new_metadata or {})},
                    metadata_changed=False,
                )
        
        # Case 5: Detect move
        if old_document.get("storage_path") and file_path:
            move_detected = self._detect_move(
                old_document.get("storage_path", ""),
                file_path,
            )
            if move_detected:
                logger.info("Document %d moved: %s -> %s", document_id,
                           old_document.get("storage_path"), file_path)
                return DocumentChange(
                    document_id=document_id,
                    change_type=ChangeType.MOVED,
                    old_state=old_document,
                    new_state={"storage_path": file_path, **(new_metadata or {})},
                    metadata_changed=False,
                )
        
        # Case 6: Compare content and metadata
        return await self._compare_content(
            document_id=document_id,
            file_path=file_path,
            old_document=old_document,
            new_chunks=new_chunks or [],
            new_metadata=new_metadata or {},
        )
    
    async def _check_corruption(
        self,
        file_path: str,
        old_document: Dict[str, Any],
    ) -> bool:
        """
        Check if file is corrupted.
        
        Args:
            file_path: Path to file
            old_document: Previous document state
            
        Returns:
            True if file is corrupted
        """
        try:
            old_hash = old_document.get("file_hash")
            if not old_hash:
                return False
            
            from app.incremental.hashing import verify_file_integrity
            return not verify_file_integrity(file_path, old_hash)
        except Exception as exc:
            logger.error("Corruption check failed: %s", exc)
            return False
    
    def _detect_rename(
        self,
        old_path: str,
        new_path: str,
        old_hash: str,
    ) -> bool:
        """
        Detect if document was renamed.
        
        Args:
            old_path: Previous file path
            new_path: Current file path
            old_hash: Previous file hash
            
        Returns:
            True if rename detected
        """
        if not self._config.enable_rename_detection:
            return False
        
        # Different filenames in same directory
        old_p = Path(old_path)
        new_p = Path(new_path)
        
        if old_p.parent == new_p.parent:
            if old_p.name != new_p.name:
                # Same content, different name = rename
                return True
        return False
    
    def _detect_move(
        self,
        old_path: str,
        new_path: str,
    ) -> bool:
        """
        Detect if document was moved.
        
        Args:
            old_path: Previous file path
            new_path: Current file path
            
        Returns:
            True if move detected
        """
        if not self._config.enable_move_detection:
            return False
        
        # Same filename, different directory
        old_p = Path(old_path)
        new_p = Path(new_path)
        
        if old_p.name == new_p.name and old_p.parent != new_p.parent:
            return True
        return False
    
    async def _compare_content(
        self,
        document_id: int,
        file_path: Optional[str],
        old_document: Dict[str, Any],
        new_chunks: List[str],
        new_metadata: Dict[str, Any],
    ) -> DocumentChange:
        """
        Compare document content and metadata.
        
        Args:
            document_id: Document identifier
            file_path: Path to document file
            old_document: Previous document state
            new_chunks: Current text chunks
            new_metadata: Current metadata
            
        Returns:
            DocumentChange describing differences
        """
        old_file_hash = old_document.get("file_hash")
        old_metadata_hash = old_document.get("metadata_hash")
        
        # Calculate new hashes
        new_file_hash = None
        new_metadata_hash = None
        
        if file_path and Path(file_path).exists():
            from app.incremental.hashing import calculate_document_hash
            new_file_hash = calculate_document_hash(file_path, new_metadata)
        
        new_metadata_hash = calculate_metadata_hash(new_metadata)
        
        # Check if metadata changed
        metadata_changed = (
            old_metadata_hash is not None and
            new_metadata_hash is not None and
            compare_hashes(old_metadata_hash, new_metadata_hash)
        )
        
        # If only metadata changed, return early
        if not metadata_changed and old_file_hash == new_file_hash:
            return DocumentChange(
                document_id=document_id,
                change_type=ChangeType.UNCHANGED,
                old_state=old_document,
                new_state=new_metadata,
                metadata_changed=False,
            )
        
        # Metadata-only change
        if old_file_hash == new_file_hash and metadata_changed:
            return DocumentChange(
                document_id=document_id,
                change_type=ChangeType.MODIFIED,
                old_state=old_document,
                new_state=new_metadata,
                metadata_changed=True,
                changed_chunks=[],  # No content change
                unchanged_chunks=list(range(len(new_chunks))),
                requires_vector_regeneration=False,
            )
        
        # Content changed - compare chunks
        old_chunks = old_document.get("chunks", [])
        old_chunk_hashes = old_document.get("chunk_hashes", [])
        
        chunk_comparison = self._compare_chunks(
            old_chunks=old_chunks,
            old_chunk_hashes=old_chunk_hashes,
            new_chunks=new_chunks,
        )
        
        # Determine if full reindex is needed
        requires_full = (
            len(chunk_comparison["new_chunks"]) > self._config.max_batch_size or
            len(chunk_comparison["changed_chunks"]) > len(old_chunks) * 0.5
        )
        
        logger.info(
            "Document %d changed: %d new, %d changed, %d unchanged, %d removed chunks",
            document_id,
            len(chunk_comparison["new_chunks"]),
            len(chunk_comparison["changed_chunks"]),
            len(chunk_comparison["unchanged_chunks"]),
            len(chunk_comparison["removed_chunks"]),
        )
        
        return DocumentChange(
            document_id=document_id,
            change_type=ChangeType.MODIFIED,
            old_state=old_document,
            new_state=new_metadata,
            changed_chunks=chunk_comparison["changed_chunks"],
            unchanged_chunks=chunk_comparison["unchanged_chunks"],
            new_chunks=chunk_comparison["new_chunks"],
            removed_chunks=chunk_comparison["removed_chunks"],
            metadata_changed=metadata_changed,
            requires_vector_regeneration=True,
            requires_full_reindex=requires_full,
        )
    
    def _compare_chunks(
        self,
        old_chunks: List[str],
        old_chunk_hashes: List[str],
        new_chunks: List[str],
    ) -> Dict[str, List[int]]:
        """
        Compare old and new chunks to detect changes.
        
        Args:
            old_chunks: Previous chunk contents
            old_chunk_hashes: Previous chunk hashes
            new_chunks: Current chunk contents
            
        Returns:
            Dictionary with lists of changed, unchanged, new, removed chunk indices
        """
        changed = []
        unchanged = []
        new = []
        removed = list(range(len(old_chunks)))
        
        # Compare by index first
        max_len = max(len(old_chunks), len(new_chunks))
        
        for idx in range(max_len):
            if idx >= len(new_chunks):
                # Chunk was removed
                continue
            
            if idx >= len(old_chunks):
                # New chunk
                new.append(idx)
                continue
            
            # Compare chunks
            old_chunks[idx]
            new_chunk = new_chunks[idx]
            old_hash = old_chunk_hashes[idx] if idx < len(old_chunk_hashes) else None
            
            new_hash = calculate_chunk_hash(new_chunk, idx)
            
            if old_hash and old_hash == new_hash:
                unchanged.append(idx)
                if idx in removed:
                    removed.remove(idx)
            else:
                changed.append(idx)
                if idx in removed:
                    removed.remove(idx)
        
        return {
            "changed_chunks": changed,
            "unchanged_chunks": unchanged,
            "new_chunks": new,
            "removed_chunks": removed,
        }


class MetadataComparator:
    """Compares document metadata to detect changes."""

    @staticmethod
    def compare(
        old_metadata: Dict[str, Any],
        new_metadata: Dict[str, Any],
        fields_to_compare: Optional[List[str]] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Compare two metadata dictionaries.
        
        Args:
            old_metadata: Previous metadata
            new_metadata: Current metadata
            fields_to_compare: Specific fields to compare (None for all)
            
        Returns:
            Tuple of (changed, changes_dict)
        """
        if not fields_to_compare:
            fields_to_compare = list(old_metadata.keys())
        
        changes = {}
        
        for field in fields_to_compare:
            old_value = old_metadata.get(field)
            new_value = new_metadata.get(field)
            
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                }
        
        return bool(changes), changes