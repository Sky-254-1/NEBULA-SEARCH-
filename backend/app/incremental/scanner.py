"""Document scanner for incremental re-indexing."""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.config import get_settings
from app.incremental.config import (
    IncrementalConfig,
    get_incremental_config,
)
from app.incremental.hashing import (
    calculate_file_hash,
    calculate_metadata_hash,
)

logger = logging.getLogger("nebula.incremental.scanner")


class ScanResult:
    """Result of document scan."""
    
    def __init__(
        self,
        document_id: int,
        file_path: str,
        status: str,
        change_type: str = "unchanged",
        file_hash: Optional[str] = None,
        metadata_hash: Optional[str] = None,
        file_size: int = 0,
        last_modified: str = "",
        chunks: List[str] = None,
        metadata: Dict[str, Any] = None,
        error: Optional[str] = None,
    ):
        self.document_id = document_id
        self.file_path = file_path
        self.status = status
        self.change_type = change_type
        self.file_hash = file_hash
        self.metadata_hash = metadata_hash
        self.file_size = file_size
        self.last_modified = last_modified
        self.chunks = chunks or []
        self.metadata = metadata or {}
        self.error = error
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "file_path": self.file_path,
            "status": self.status,
            "change_type": self.change_type,
            "file_hash": self.file_hash,
            "metadata_hash": self.metadata_hash,
            "file_size": self.file_size,
            "last_modified": self.last_modified,
            "chunk_count": len(self.chunks),
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class DocumentScanner:
    """
    Scans documents to detect changes for incremental re-indexing.
    
    Compares file state against database to determine if re-indexing is needed.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize document scanner."""
        self._config = config or get_incremental_config()
        self._settings = get_settings()
    
    async def scan_document(
        self,
        document_id: int,
        file_path: Optional[str] = None,
        old_document: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """
        Scan a single document.
        
        Args:
            document_id: Document identifier
            file_path: Path to document file
            old_document: Previous document state from database
            metadata: Current document metadata
            
        Returns:
            ScanResult with scan findings
        """
        # If no file path, mark as deleted
        if not file_path:
            if old_document:
                return ScanResult(
                    document_id=document_id,
                    file_path=old_document.get("storage_path", ""),
                    status="deleted",
                    change_type="deleted",
                    error="File path not found",
                )
            else:
                return ScanResult(
                    document_id=document_id,
                    file_path="",
                    status="skipped",
                    error="No file path available",
                )
        
        # Check if file exists
        if not Path(file_path).exists():
            return ScanResult(
                document_id=document_id,
                file_path=file_path,
                status="not_found",
                change_type="deleted",
                error="File does not exist",
            )
        
        try:
            # Get file stats
            file_size = os.path.getsize(file_path)
            last_modified = datetime.fromtimestamp(
                Path(file_path).stat().st_mtime
            ).isoformat()
            
            # Check file size first (quick check)
            if old_document and old_document.get("file_size") == file_size:
                # Same size - check hash if enabled
                if old_document.get("last_modified") == last_modified:
                    # Same modification time - likely unchanged
                    return ScanResult(
                        document_id=document_id,
                        file_path=file_path,
                        status="unchanged",
                        change_type="unchanged",
                        file_hash=old_document.get("file_hash"),
                        metadata_hash=old_document.get("metadata_hash"),
                        file_size=file_size,
                        last_modified=last_modified,
                        chunks=old_document.get("chunks", []),
                        metadata=old_document.get("metadata", {}),
                    )
            
            # Calculate file hash
            file_hash = calculate_file_hash(file_path)
            new_metadata_hash = None
            
            # Compare with old state
            if old_document:
                old_file_hash = old_document.get("file_hash")
                old_metadata_hash = old_document.get("metadata_hash") if metadata else None
                
                # Calculate metadata hash if metadata provided
                if metadata:
                    new_metadata_hash = calculate_metadata_hash(metadata)
                else:
                    new_metadata_hash = old_metadata_hash
                
                # Check if content changed
                if old_file_hash and file_hash == old_file_hash:
                    # Content unchanged
                    if old_metadata_hash == new_metadata_hash:
                        change_type = "unchanged"
                    else:
                        change_type = "modified"
                else:
                    # Content changed
                    change_type = "modified"
            else:
                # New document
                change_type = "new"
                old_metadata_hash = None
            
            return ScanResult(
                document_id=document_id,
                file_path=file_path,
                status="scanned",
                change_type=change_type,
                file_hash=file_hash,
                metadata_hash=new_metadata_hash if metadata else old_metadata_hash,
                file_size=file_size,
                last_modified=last_modified,
                metadata=metadata or {},
            )
            
        except Exception as exc:
            logger.error("Error scanning document %d: %s", document_id, exc)
            return ScanResult(
                document_id=document_id,
                file_path=file_path,
                status="error",
                change_type="skipped",
                error=str(exc),
            )
    
    async def scan_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[ScanResult]:
        """
        Scan multiple documents.
        
        Args:
            documents: List of document dictionaries with id, file_path, metadata
            
        Returns:
            List of ScanResults
        """
        results = []
        
        # Process in batches
        batch_size = self._config.scan_batch_size
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Scan batch concurrently
            tasks = []
            for doc in batch:
                task = self.scan_document(
                    document_id=doc["id"],
                    file_path=doc.get("storage_path"),
                    old_document=doc.get("db_state"),
                    metadata=doc.get("metadata"),
                )
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error("Batch scan error: %s", result)
                else:
                    results.append(result)
        
        return results
    
    async def scan_all(
        self,
        db_session,
        batch_size: int = 100,
    ) -> List[ScanResult]:
        """
        Scan all documents in database.
        
        Args:
            db_session: Database session
            batch_size: Number of documents per batch
            
        Returns:
            List of ScanResults
        """
        results = []
        
        try:
            # Get all documents from database
            cursor = await db_session.execute(
                "SELECT id, storage_path, metadata FROM documents"
            )
            rows = await cursor.fetchall()
            
            documents = []
            for row in rows:
                doc_id, storage_path, metadata_json = row
                documents.append({
                    "id": doc_id,
                    "storage_path": storage_path,
                    "metadata": metadata_json,
                    "db_state": None,  # Will be populated by scan_document
                })
            
            # Scan all documents
            results = await self.scan_batch(documents)
            
        except Exception as exc:
            logger.error("Error scanning all documents: %s", exc)
        
        return results


class FileWatcher:
    """
    Watches filesystem for changes.
    
    Detects created, modified, deleted, renamed, and moved files.
    """

    def __init__(self, config: Optional[IncrementalConfig] = None):
        """Initialize file watcher."""
        self._config = config or get_incremental_config()
        self._watched_paths: Set[str] = set()
        self._file_states: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, path: str) -> None:
        """
        Start watching a path.
        
        Args:
            path: Path to watch
        """
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._watch_loop())
        
        self._watched_paths.add(path)
        logger.info("Started watching path: %s", path)
    
    async def stop(self) -> None:
        """Stop watching."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped file watcher")
    
    async def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                await asyncio.sleep(self._config.debounce_seconds)
                
                # Check for changes in watched paths
                for path in self._watched_paths:
                    await self._check_changes(path)
                    
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Watch loop error: %s", exc)
    
    async def _check_changes(self, path: str) -> None:
        """
        Check for changes in watched path.
        
        Args:
            path: Path to check
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return
            
            # Get current state
            current_files: Dict[str, Dict[str, Any]] = {}
            
            for file_path in path_obj.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    current_files[str(file_path)] = {
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    }
            
            # Detect changes
            added = []
            modified = []
            deleted = []
            
            # Check for added/modified files
            for file_path, state in current_files.items():
                if file_path not in self._file_states:
                    # New file
                    added.append(file_path)
                elif self._file_states[file_path] != state:
                    # Modified file
                    modified.append(file_path)
            
            # Check for deleted files
            for file_path in self._file_states:
                if file_path not in current_files:
                    deleted.append(file_path)
            
            # Update state
            self._file_states = current_files
            
            # Emit events (simplified - would integrate with event system)
            if added:
                logger.info("Files added: %s", added)
            if modified:
                logger.info("Files modified: %s", modified)
            if deleted:
                logger.info("Files deleted: %s", deleted)
                
        except Exception as exc:
            logger.error("Error checking changes in %s: %s", path, exc)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current watcher state."""
        return {
            "watched_paths": list(self._watched_paths),
            "tracked_files": len(self._file_states),
            "running": self._running,
        }