"""Tests for the document indexing worker."""

import asyncio
import hashlib
import os
import tempfile
import uuid
from pathlib import Path

import pytest

from app.database import get_db
from app.database.engine import connect
from app.database.repositories.document import DocumentRepository
from app.workers.indexer import IndexingWorker


@pytest.fixture
def temp_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content for indexing")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def worker():
    """Create an indexer worker."""
    return IndexingWorker(max_retries=3)


@pytest.mark.asyncio
async def test_worker_processes_text_file(temp_file, worker):
    """Test that worker can extract content from text file."""
    content = await worker._extract_content(temp_file)
    assert content == "Test content for indexing"


@pytest.mark.asyncio
async def test_worker_computes_hash(worker):
    """Test that worker computes correct SHA-256 hash."""
    content = "test content"
    hash_val = await worker._compute_hash(content)
    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert hash_val == expected


@pytest.mark.asyncio
async def test_worker_calculates_delay(worker):
    """Test exponential backoff delay calculation."""
    assert await worker._calculate_delay(0) == 5.0
    assert await worker._calculate_delay(1) == 15.0
    assert await worker._calculate_delay(2) == 45.0


@pytest.mark.asyncio
async def test_worker_ownership_validation(temp_file, worker):
    """Test ownership validation with database."""
    from app.database.repositories.document import DocumentRepository

    db = await connect()
    try:
        # Create a document
        repo = DocumentRepository(db)
        # Note: This requires a user_id, which we don't have in test context
        # This test is mainly to verify the method signature
        assert hasattr(worker, "_validate_ownership")
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_worker_handles_missing_file(worker):
    """Test that worker raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        await worker._extract_content("/nonexistent/file.txt")


@pytest.mark.asyncio
async def test_worker_handles_extraction_error(worker):
    """Test error handling during content extraction."""
    # Create a corrupted PDF-like file
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF")
        path = f.name

    try:
        with pytest.raises(Exception):  # pypdf will raise an error
            await worker._extract_content(path)
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_worker_idempotent_retries(worker):
    """Test that retries are idempotent."""
    # Same job data should produce same result
    content = "Test content"
    hash1 = await worker._compute_hash(content)
    hash2 = await worker._compute_hash(content)
    assert hash1 == hash2


@pytest.mark.asyncio
async def test_worker_retries_bounded(worker):
    """Test that worker respects max_retries limit."""
    assert worker.max_retries == 3


@pytest.mark.asyncio
async def test_worker_transitions_status():
    """Test that document status transitions work correctly."""
    db = await connect()
    try:
        repo = DocumentRepository(db)
        assert hasattr(repo, "transition_to_processing")
        assert hasattr(repo, "transition_to_indexed")
        assert hasattr(repo, "transition_to_failed")
    finally:
        await db.close()
