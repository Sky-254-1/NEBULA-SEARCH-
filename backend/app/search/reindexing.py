"""
Incremental Re-indexing System

Provides efficient document update handling:
- Change detection
- Version tracking
- Timestamp management
- Partial re-indexing
- Full re-index capability
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger("nebula.search.reindexing")
settings = get_settings()


class ReindexStatus(str, Enum):
    """Re-indexing status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ChangeType(str, Enum):
    """Types of document changes"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    METADATA_CHANGED = "metadata_changed"


@dataclass
class DocumentVersion:
    """Document version tracking"""
    document_id: str
    version: int
    checksum: str
    timestamp: datetime
    change_type: ChangeType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReindexTask:
    """Re-indexing task"""
    id: str
    document_ids: List[str]
    status: ReindexStatus
    is_full_reindex: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    processed_count: int = 0
    total_count: int = 0
    error_message: Optional[str] = None


class IncrementalReindexer:
    """
    Incremental re-indexing system.
    
    Features:
    - Change detection via checksums
    - Version tracking
    - Timestamp-based incremental updates
    - Partial and full re-indexing
    - Batch processing
    """

    def __init__(self):
        self.versions: Dict[str, DocumentVersion] = {}
        self.tasks: Dict[str, ReindexTask] = {}
        self.status = ReindexStatus.IDLE
        self.batch_size = 100

    async def detect_changes(
        self, documents: List[Dict[str, Any]]
    ) -> List[DocumentVersion]:
        """
        Detect changes in documents.
        
        Args:
            documents: List of documents with id, content, checksum, updated_at
            
        Returns:
            List of changed documents
        """
        changes = []
        
        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                continue
            
            # Calculate current checksum
            content = doc.get("content", "")
            current_checksum = hashlib.sha256(content.encode()).hexdigest()
            current_version = doc.get("version", 1)
            updated_at = doc.get("updated_at", datetime.utcnow())
            
            # Check if document exists in version tracking
            if doc_id in self.versions:
                existing = self.versions[doc_id]
                
                # Check if content changed
                if existing.checksum != current_checksum:
                    changes.append(DocumentVersion(
                        document_id=doc_id,
                        version=current_version,
                        checksum=current_checksum,
                        timestamp=updated_at,
                        change_type=ChangeType.UPDATED,
                    ))
                # Check if metadata changed
                elif existing.metadata != doc.get("metadata", {}):
                    changes.append(DocumentVersion(
                        document_id=doc_id,
                        version=current_version,
                        checksum=current_checksum,
                        timestamp=updated_at,
                        change_type=ChangeType.METADATA_CHANGED,
                    ))
            else:
                # New document
                changes.append(DocumentVersion(
                    document_id=doc_id,
                    version=current_version,
                    checksum=current_checksum,
                    timestamp=updated_at,
                    change_type=ChangeType.CREATED,
                ))
        
        return changes

    async def reindex_changes(
        self, changes: List[DocumentVersion]
    ) -> ReindexTask:
        """
        Re-index changed documents.
        
        Args:
            changes: List of document changes
            
        Returns:
            ReindexTask instance
        """
        task = ReindexTask(
            id=f"reindex-{datetime.utcnow().timestamp()}",
            document_ids=[c.document_id for c in changes],
            status=ReindexStatus.RUNNING,
            is_full_reindex=False,
            started_at=datetime.utcnow(),
            total_count=len(changes),
        )
        
        self.tasks[task.id] = task
        self.status = ReindexStatus.RUNNING
        
        try:
            # Process in batches
            for i in range(0, len(changes), self.batch_size):
                batch = changes[i:i + self.batch_size]
                
                # Process batch
                await self._process_batch(batch)
                
                # Update progress
                task.processed_count += len(batch)
                task.progress = task.processed_count / task.total_count
                
                logger.info(
                    f"Re-indexing progress: {task.processed_count}/{task.total_count}"
                )
            
            task.status = ReindexStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.status = ReindexStatus.IDLE
            
            logger.info(f"Re-indexing completed: {task.processed_count} documents")
            
        except Exception as e:
            task.status = ReindexStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            self.status = ReindexStatus.IDLE
            
            logger.error(f"Re-indexing failed: {e}", exc_info=True)
        
        return task

    async def full_reindex(self) -> ReindexTask:
        """
        Perform full re-index of all documents.
        
        Returns:
            ReindexTask instance
        """
        task = ReindexTask(
            id=f"full-reindex-{datetime.utcnow().timestamp()}",
            document_ids=[],  # Will be populated from database
            status=ReindexStatus.RUNNING,
            is_full_reindex=True,
            started_at=datetime.utcnow(),
        )
        
        self.tasks[task.id] = task
        self.status = ReindexStatus.RUNNING
        
        try:
            # Get all document IDs from database
            # This would be implemented with actual database calls
            all_document_ids = await self._get_all_document_ids()
            task.document_ids = all_document_ids
            task.total_count = len(all_document_ids)
            
            # Clear version tracking
            self.versions.clear()
            
            # Process in batches
            for i in range(0, len(all_document_ids), self.batch_size):
                batch = all_document_ids[i:i + self.batch_size]
                
                # Re-index batch
                await self._reindex_batch(batch)
                
                # Update progress
                task.processed_count += len(batch)
                task.progress = task.processed_count / task.total_count
                
                logger.info(
                    f"Full re-indexing progress: {task.processed_count}/{task.total_count}"
                )
            
            task.status = ReindexStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.status = ReindexStatus.IDLE
            
            logger.info(f"Full re-indexing completed: {task.processed_count} documents")
            
        except Exception as e:
            task.status = ReindexStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            self.status = ReindexStatus.IDLE
            
            logger.error(f"Full re-indexing failed: {e}", exc_info=True)
        
        return task

    async def _process_batch(self, changes: List[DocumentVersion]):
        """Process a batch of changes"""
        for change in changes:
            try:
                # Update version tracking
                self.versions[change.document_id] = change
                
                # Queue document for re-indexing
                from app.search.indexing import indexing_manager
                await indexing_manager.index_document(
                    document_id=change.document_id,
                    priority=JobPriority.HIGH if change.change_type == ChangeType.DELETED else JobPriority.NORMAL,
                )
                
            except Exception as e:
                logger.error(f"Failed to process change for {change.document_id}: {e}")

    async def _reindex_batch(self, document_ids: List[str]):
        """Re-index a batch of documents"""
        for doc_id in document_ids:
            try:
                # Get document from database
                doc = await self._get_document(doc_id)
                if not doc:
                    continue
                
                # Calculate checksum
                content = doc.get("content", "")
                checksum = hashlib.sha256(content.encode()).hexdigest()
                
                # Update version tracking
                self.versions[doc_id] = DocumentVersion(
                    document_id=doc_id,
                    version=doc.get("version", 1),
                    checksum=checksum,
                    timestamp=doc.get("updated_at", datetime.utcnow()),
                    change_type=ChangeType.UPDATED,
                )
                
                # Queue for indexing
                from app.search.indexing import indexing_manager
                await indexing_manager.index_document(
                    document_id=doc_id,
                    priority=JobPriority.NORMAL,
                )
                
            except Exception as e:
                logger.error(f"Failed to re-index document {doc_id}: {e}")

    async def _get_all_document_ids(self) -> List[str]:
        """Get all document IDs from database"""
        # This would be implemented with actual database calls
        # For now, return empty list
        return []

    async def _get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from database"""
        # This would be implemented with actual database calls
        # For now, return None
        return None

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get re-indexing task status"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "status": task.status.value,
            "is_full_reindex": task.is_full_reindex,
            "progress": task.progress,
            "processed_count": task.processed_count,
            "total_count": task.total_count,
            "error_message": task.error_message,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get re-indexing system status"""
        return {
            "status": self.status.value,
            "total_versions_tracked": len(self.versions),
            "total_tasks": len(self.tasks),
        }


# Import JobPriority from indexing module
from app.search.indexing import JobPriority

# Global instance
incremental_reindexer = IncrementalReindexer()