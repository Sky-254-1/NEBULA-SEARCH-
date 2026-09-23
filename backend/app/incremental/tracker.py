"""Index tracking for incremental re-indexing."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)

logger = logging.getLogger("nebula.incremental.tracker")


class IndexStatus(str, Enum):
    """Index status enumeration."""
    PENDING = "pending"
    SCANNING = "scanning"
    DETECTING = "detecting"
    INDEXING = "indexing"
    SYNCHRONIZING = "synchronizing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IndexRecord:
    """Record of document index state."""
    document_id: int
    status: IndexStatus
    file_hash: str = ""
    metadata_hash: str = ""
    chunk_hashes: List[str] = field(default_factory=list)
    chunk_count: int = 0
    embedding_count: int = 0
    last_indexed: str = ""
    last_scanned: str = ""
    last_modified: str = ""
    version: int = 1
    index_generation: int = 1
    sync_status: str = "synced"
    error_message: Optional[str] = None


class IndexTracker:
    """
    Tracks document index state for incremental updates.
    
    Maintains history of document hashes and index states to detect changes.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize index tracker."""
        self._config = config or get_incremental_config()
        self._records: Dict[int, IndexRecord] = {}
    
    async def initialize_document(
        self,
        db_session,
        document_id: int,
        file_path: str,
        chunks: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize tracking for a new document.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            file_path: Path to document file
            chunks: List of text chunks
            embeddings: Optional list of embeddings
            metadata: Optional document metadata
        """
        # Import here to avoid circular dependency
        from app.incremental.hashing import (
            calculate_document_hash,
            calculate_metadata_hash,
            calculate_chunk_hash,
        )
        
        # Calculate hashes
        file_hash = calculate_document_hash(file_path, metadata)
        metadata_hash = calculate_metadata_hash(metadata or {})
        chunk_hashes = [calculate_chunk_hash(chunk, idx) for idx, chunk in enumerate(chunks)]
        
        # Create record
        record = IndexRecord(
            document_id=document_id,
            status=IndexStatus.COMPLETED,
            file_hash=file_hash,
            metadata_hash=metadata_hash,
            chunk_hashes=chunk_hashes,
            chunk_count=len(chunks),
            embedding_count=len(embeddings) if embeddings else 0,
            last_indexed=datetime.now().isoformat(),
            last_scanned=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
        )
        
        self._records[document_id] = record
        
        # Persist to database
        await self._persist_record(db_session, record)
        
        logger.info("Initialized index tracking for document %d", document_id)
    
    async def update_status(
        self,
        db_session,
        document_id: int,
        status: IndexStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update document index status.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            status: New status
            error_message: Optional error message
        """
        if document_id in self._records:
            self._records[document_id].status = status
            if error_message:
                self._records[document_id].error_message = error_message
        
        # Persist to database
        await self._update_status(db_session, document_id, status, error_message)
        
        logger.debug("Updated status for document %d to %s", document_id, status)
    
    async def record_scan(
        self,
        db_session,
        document_id: int,
        file_hash: str,
        metadata_hash: str,
        last_modified: str,
    ) -> None:
        """
        Record scan results.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            file_hash: File checksum
            metadata_hash: Metadata checksum
            last_modified: Last modified timestamp
        """
        if document_id in self._records:
            record = self._records[document_id]
            record.file_hash = file_hash
            record.metadata_hash = metadata_hash
            record.last_scanned = datetime.now().isoformat()
            record.last_modified = last_modified
        else:
            # Create new record
            self._records[document_id] = IndexRecord(
                document_id=document_id,
                status=IndexStatus.PENDING,
                file_hash=file_hash,
                metadata_hash=metadata_hash,
                last_scanned=datetime.now().isoformat(),
                last_modified=last_modified,
            )
        
        # Persist to database
        await self._persist_record(db_session, self._records[document_id])
        
        logger.debug("Recorded scan for document %d", document_id)
    
    async def get_record(self, document_id: int) -> Optional[IndexRecord]:
        """
        Get index record for document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            IndexRecord or None
        """
        return self._records.get(document_id)
    
    async def get_all_records(self) -> List[IndexRecord]:
        """
        Get all index records.
        
        Returns:
            List of IndexRecords
        """
        return list(self._records.values())
    
    async def needs_reindex(self, document_id: int, new_file_hash: str) -> bool:
        """
        Check if document needs re-indexing.
        
        Args:
            document_id: Document identifier
            new_file_hash: New file checksum
            
        Returns:
            True if re-indexing needed
        """
        record = self._records.get(document_id)
        
        if not record:
            return True
        
        return record.file_hash != new_file_hash
    
    async def increment_version(self, db_session, document_id: int) -> int:
        """
        Increment document version.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            
        Returns:
            New version number
        """
        if document_id in self._records:
            record = self._records[document_id]
            record.version += 1
            record.last_indexed = datetime.now().isoformat()
        
        # Persist to database
        await self._persist_record(db_session, self._records[document_id])
        
        logger.debug("Incremented version for document %d to %d", document_id, 
                    self._records[document_id].version if document_id in self._records else 1)
        
        return self._records[document_id].version if document_id in self._records else 1
    
    async def _persist_record(self, db_session, record: IndexRecord) -> None:
        """
        Persist record to database.
        
        Args:
            db_session: Database session
            record: IndexRecord to persist
        """
        try:
            # Check if record exists
            cursor = await db_session.execute(
                "SELECT id FROM index_tracking WHERE document_id = ?",
                (record.document_id,),
            )
            row = await cursor.fetchone()
            
            chunk_hashes_json = ",".join(record.chunk_hashes)
            
            if row:
                # Update existing record
                await db_session.execute(
                    """
                    UPDATE index_tracking
                    SET file_hash = ?, metadata_hash = ?, chunk_hashes = ?,
                        chunk_count = ?, embedding_count = ?, last_indexed = ?,
                        last_scanned = ?, last_modified = ?, version = ?,
                        index_generation = ?, sync_status = ?, error_message = ?
                    WHERE document_id = ?
                    """,
                    (
                        record.file_hash,
                        record.metadata_hash,
                        chunk_hashes_json,
                        record.chunk_count,
                        record.embedding_count,
                        record.last_indexed,
                        record.last_scanned,
                        record.last_modified,
                        record.version,
                        record.index_generation,
                        record.sync_status,
                        record.error_message,
                        record.document_id,
                    ),
                )
            else:
                # Insert new record
                await db_session.execute(
                    """
                    INSERT INTO index_tracking
                    (document_id, file_hash, metadata_hash, chunk_hashes,
                     chunk_count, embedding_count, last_indexed, last_scanned,
                     last_modified, version, index_generation, sync_status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.document_id,
                        record.file_hash,
                        record.metadata_hash,
                        chunk_hashes_json,
                        record.chunk_count,
                        record.embedding_count,
                        record.last_indexed,
                        record.last_scanned,
                        record.last_modified,
                        record.version,
                        record.index_generation,
                        record.sync_status,
                        record.error_message,
                    ),
                )
            
            await db_session.commit()
            
        except Exception as exc:
            logger.error("Failed to persist index record for document %d: %s", 
                        record.document_id, exc)
            raise
    
    async def _update_status(
        self,
        db_session,
        document_id: int,
        status: IndexStatus,
        error_message: Optional[str],
    ) -> None:
        """
        Update status in database.
        
        Args:
            db_session: Database session
            document_id: Document identifier
            status: New status
            error_message: Optional error message
        """
        try:
            await db_session.execute(
                "UPDATE index_tracking SET sync_status = ?, error_message = ? WHERE document_id = ?",
                (status.value, error_message, document_id),
            )
            await db_session.commit()
        except Exception as exc:
            logger.error("Failed to update status for document %d: %s", document_id, exc)