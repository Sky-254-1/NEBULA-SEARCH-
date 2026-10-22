"""Task definitions for indexing jobs."""

import hashlib
import logging
import mimetypes
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import get_settings
from app.indexing.config import (
    JobPriority,
)
from app.indexing.queue import indexing_queue

logger = logging.getLogger("nebula.indexing.tasks")
settings = get_settings()


class TaskType:
    """Task type constants."""
    INDEX_DOCUMENT = "index_document"
    REINDEX_DOCUMENT = "reindex_document"
    DELETE_DOCUMENT = "delete_document"
    OPTIMIZE_INDEX = "optimize_index"


@dataclass
class IndexTask:
    """Indexing task definition."""
    task_id: str
    task_type: str
    document_id: int
    user_id: Optional[int] = None
    filename: str = ""
    priority: str = JobPriority.NORMAL
    payload: Dict[str, Any] = None
    created_at: float = 0.0
    
    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}
        if self.created_at == 0.0:
            self.created_at = time.time()


class TaskBuilder:
    """Builds indexing tasks."""
    
    @staticmethod
    def create_index_task(
        document_id: int,
        user_id: Optional[int] = None,
        filename: str = "",
        file_path: Optional[str] = None,
        priority: str = JobPriority.NORMAL,
    ) -> IndexTask:
        """
        Create an index task for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID
            filename: Document filename
            file_path: Path to document file
            priority: Task priority
            
        Returns:
            IndexTask
        """
        task_id = str(uuid.uuid4())
        payload = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "file_path": file_path,
        }
        
        return IndexTask(
            task_id=task_id,
            task_type=TaskType.INDEX_DOCUMENT,
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            priority=priority,
            payload=payload,
        )
    
    @staticmethod
    def create_reindex_task(
        document_id: int,
        user_id: Optional[int] = None,
        filename: str = "",
        incremental: bool = True,
        priority: str = JobPriority.NORMAL,
    ) -> IndexTask:
        """
        Create a reindex task.
        
        Args:
            document_id: Document ID
            user_id: User ID
            filename: Document filename
            incremental: Whether to use incremental indexing
            priority: Task priority
            
        Returns:
            IndexTask
        """
        task_id = str(uuid.uuid4())
        payload = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "incremental": incremental,
        }
        
        return IndexTask(
            task_id=task_id,
            task_type=TaskType.REINDEX_DOCUMENT,
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            priority=priority,
            payload=payload,
        )


def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex checksum
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def detect_file_type(filename: str) -> str:
    """Detect file type from filename."""
    ext = Path(filename).suffix.lower()
    mime_type, _ = mimetypes.guess_type(filename)
    
    type_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
        ".html": "html",
        ".csv": "csv",
        ".json": "json",
    }
    
    return type_map.get(ext, mime_type or "unknown")


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        # Try to break at word boundary
        if end < text_length:
            search_start = max(start, end - 100)
            for i in range(end, search_start, -1):
                if text[i].isspace():
                    end = i + 1
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap (ensure forward progress to prevent infinite loops)
        start = max(start + 1, end - chunk_overlap)
        if start >= text_length:
            break

    return chunks


def calculate_chunk_hash(content: str) -> str:
    """Calculate hash for chunk content."""
    return hashlib.sha256(content.encode()).hexdigest()


async def submit_index_task(
    document_id: int,
    user_id: Optional[int] = None,
    filename: str = "",
    file_path: Optional[str] = None,
    priority: str = JobPriority.NORMAL,
) -> str:
    """
    Submit document for indexing.
    
    Args:
        document_id: Document ID
        user_id: User ID
        filename: Document filename
        file_path: Path to file
        priority: Index priority
        
    Returns:
        job_id: Job identifier
        
    Raises:
        QueueError: If queue is full
    """
    task = TaskBuilder.create_index_task(
        document_id=document_id,
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        priority=priority,
    )
    
    job = {
        "job_id": task.task_id,
        "type": task.task_type,
        "document_id": task.document_id,
        "user_id": task.user_id,
        "filename": task.filename,
        "priority": task.priority,
        "payload": task.payload,
        "created_at": task.created_at,
        "retry_count": 0,
    }
    
    return await indexing_queue.enqueue(job)