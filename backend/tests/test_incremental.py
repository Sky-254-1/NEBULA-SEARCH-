"""Comprehensive tests for incremental re-indexing system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.incremental.config import (
    IncrementalConfig,
    IncrementalReindexMode,
    ReindexJobConfig,
)
from app.incremental.hashing import (
    calculate_document_hash,
    calculate_metadata_hash,
    calculate_chunk_hash,
    calculate_vector_hash,
    compare_hashes,
    verify_file_integrity,
)
from app.incremental.detector import (
    ChangeDetector,
    ChangeType,
    DocumentChange,
)
from app.incremental.diff import (
    DiffEngine,
    ChunkDiff,
    DocumentDiff,
    DiffOperationType,
)
from app.incremental.scanner import (
    DocumentScanner,
    ScanResult,
    FileWatcher,
)
from app.incremental.synchronizer import (
    IncrementalSynchronizer,
    SyncResult,
)
from app.incremental.metadata import (
    MetadataSynchronizer,
    MetadataTracker,
)
from app.incremental.tracker import (
    IndexTracker,
    IndexStatus,
    IndexRecord,
)
from app.incremental.cleanup import (
    CleanupService,
)
from app.incremental.events import (
    IncrementalEvent,
    IncrementalEventType,
    MetricsCollector,
    get_event_manager,
    reset_event_manager,
)
from app.incremental.scheduler import (
    IncrementalScheduler,
)
from app.incremental.services import (
    IncrementalIndexingService,
)


# ==================== Hashing Tests ====================

class TestHashing:
    """Tests for hashing utilities."""

    def test_calculate_string_hash(self, tmp_path):
        """Test string hashing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        hash1 = calculate_document_hash(str(test_file))
        hash2 = calculate_document_hash(str(test_file))
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_calculate_string_hash_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        file_a = tmp_path / "a.txt"
        file_b = tmp_path / "b.txt"
        file_a.write_text("content A", encoding="utf-8")
        file_b.write_text("content B", encoding="utf-8")
        hash1 = calculate_document_hash(str(file_a))
        hash2 = calculate_document_hash(str(file_b))
        assert hash1 != hash2

    def test_calculate_metadata_hash(self):
        """Test metadata hashing."""
        metadata1 = {"title": "Doc 1", "author": "Alice", "tags": ["tech"]}
        metadata2 = {"title": "Doc 1", "author": "Alice", "tags": ["tech"]}
        metadata3 = {"title": "Doc 2", "author": "Bob", "tags": ["science"]}
        
        hash1 = calculate_metadata_hash(metadata1)
        hash2 = calculate_metadata_hash(metadata2)
        hash3 = calculate_metadata_hash(metadata3)
        
        assert hash1 == hash2
        assert hash1 != hash3

    def test_calculate_chunk_hash(self):
        """Test chunk hashing."""
        content = "This is a test chunk"
        hash1 = calculate_chunk_hash(content, 0)
        hash2 = calculate_chunk_hash(content, 0)
        hash3 = calculate_chunk_hash(content, 1)
        
        assert hash1 == hash2
        assert hash1 != hash3  # Different index

    def test_calculate_vector_hash(self):
        """Test vector hashing."""
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.1, 0.2, 0.3]
        embedding3 = [0.4, 0.5, 0.6]
        
        hash1 = calculate_vector_hash(embedding1, "chunk_0")
        hash2 = calculate_vector_hash(embedding2, "chunk_0")
        hash3 = calculate_vector_hash(embedding3, "chunk_0")
        
        assert hash1 == hash2
        assert hash1 != hash3

    def test_compare_hashes(self):
        """Test hash comparison."""
        assert compare_hashes("hash1", "hash2") is True
        assert compare_hashes("hash1", "hash1") is False

    def test_verify_file_integrity(self, tmp_path):
        """Test file integrity verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_hash = calculate_document_hash(str(test_file))
        assert verify_file_integrity(str(test_file), file_hash) is True
        assert verify_file_integrity(str(test_file), "wrong_hash") is False


# ==================== Change Detection Tests ====================

class TestChangeDetector:
    """Tests for change detection."""

    @pytest.fixture
    def detector(self):
        """Create change detector instance."""
        config = IncrementalConfig(enable_corruption_detection=False)
        return ChangeDetector(config)

    @pytest.mark.asyncio
    async def test_detect_new_document(self, detector):
        """Test detection of new document."""
        change = await detector.detect_changes(
            document_id=1,
            file_path="/path/to/file.txt",
            old_document=None,
            new_chunks=["chunk 1", "chunk 2"],
            new_metadata={"title": "New Document"},
        )
        
        assert change.change_type == ChangeType.NEW
        assert change.document_id == 1

    @pytest.mark.asyncio
    async     def test_detect_unchanged_document(self, detector, tmp_path):
        """Test detection of unchanged document."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        old_doc = {
            "file_hash": calculate_document_hash(str(test_file), {"title": "Test"}),
            "metadata_hash": calculate_metadata_hash({"title": "Test"}),
            "chunks": ["chunk 1"],
            "chunk_hashes": [calculate_chunk_hash("chunk 1", 0)],
        }
        
        change = await detector.detect_changes(
            document_id=1,
            file_path=str(test_file),
            old_document=old_doc,
            new_chunks=["chunk 1"],
            new_metadata={"title": "Test"},
        )
        
        assert change.change_type == ChangeType.UNCHANGED

    @pytest.mark.asyncio
    async def test_detect_modified_document(self, detector, tmp_path):
        """Test detection of modified document."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        old_doc = {
            "file_hash": calculate_document_hash(str(test_file)),
            "metadata_hash": calculate_metadata_hash({"title": "Original"}),
            "chunks": ["original chunk"],
            "chunk_hashes": [calculate_chunk_hash("original chunk", 0)],
        }
        
        # Modify file
        test_file.write_text("modified content")
        
        change = await detector.detect_changes(
            document_id=1,
            file_path=str(test_file),
            old_document=old_doc,
            new_chunks=["modified chunk"],
            new_metadata={"title": "Original"},
        )
        
        assert change.change_type == ChangeType.MODIFIED
        assert len(change.changed_chunks) == 1

    @pytest.mark.asyncio
    async def test_detect_deleted_document(self, detector):
        """Test detection of deleted document."""
        change = await detector.detect_changes(
            document_id=1,
            file_path="/nonexistent/path.txt",
            old_document={"file_hash": "abc123"},
        )
        
        assert change.change_type == ChangeType.DELETED

    @pytest.mark.asyncio
    async def test_detect_metadata_only_change(self, detector, tmp_path):
        """Test detection of metadata-only change."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        old_doc = {
            "file_hash": calculate_document_hash(str(test_file)),
            "metadata_hash": calculate_metadata_hash({"title": "Original"}),
            "chunks": ["chunk 1"],
            "chunk_hashes": [calculate_chunk_hash("chunk 1", 0)],
        }
        
        change = await detector.detect_changes(
            document_id=1,
            file_path=str(test_file),
            old_document=old_doc,
            new_chunks=["chunk 1"],
            new_metadata={"title": "Updated Title"},
        )
        
        assert change.change_type == ChangeType.MODIFIED
        assert change.metadata_changed is True
        assert len(change.changed_chunks) == 0


# ==================== Diff Tests ====================

class TestDiffEngine:
    """Tests for diff engine."""

    @pytest.fixture
    def diff_engine(self):
        """Create diff engine instance."""
        return DiffEngine()

    def test_compute_diff_no_changes(self, diff_engine):
        """Test diff with no changes."""
        expected_hash = diff_engine._compute_chunk_hash("chunk 1", 0)
        old_chunks = [{"chunk_id": 0, "content": "chunk 1", "chunk_hash": expected_hash}]
        new_chunks = ["chunk 1"]
        
        diff = diff_engine.compute_diff(
            document_id=1,
            old_chunks=old_chunks,
            new_chunks=new_chunks,
            old_metadata={"title": "Doc"},
            new_metadata={"title": "Doc"},
        )
        
        assert len(diff.reused_chunks) == 1
        assert len(diff.added_chunks) == 0
        assert len(diff.removed_chunks) == 0
        assert len(diff.modified_chunks) == 0

    def test_compute_diff_with_changes(self, diff_engine):
        """Test diff with changes."""
        old_chunks = [
            {"chunk_id": 0, "content": "old chunk 1", "chunk_hash": diff_engine._compute_chunk_hash("old chunk 1", 0)},
            {"chunk_id": 1, "content": "chunk 2", "chunk_hash": diff_engine._compute_chunk_hash("chunk 2", 1)},
        ]
        new_chunks = ["modified chunk 1", "chunk 2", "new chunk 3"]
        
        diff = diff_engine.compute_diff(
            document_id=1,
            old_chunks=old_chunks,
            new_chunks=new_chunks,
            old_metadata={"title": "Doc"},
            new_metadata={"title": "Doc"},
        )
        
        assert len(diff.modified_chunks) == 1
        assert len(diff.added_chunks) == 1
        assert len(diff.reused_chunks) == 1
        assert diff.estimated_embedding_calls == 2

    def test_compute_diff_metadata_changed(self, diff_engine):
        """Test diff with metadata changes."""
        diff = diff_engine.compute_diff(
            document_id=1,
            old_chunks=[],
            new_chunks=[],
            old_metadata={"title": "Old Title"},
            new_metadata={"title": "New Title"},
        )
        
        assert diff.metadata_changed is True
        assert "title" in diff.metadata_changes


# ==================== Scanner Tests ====================

class TestDocumentScanner:
    """Tests for document scanner."""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance."""
        return DocumentScanner()

    @pytest.mark.asyncio
    async def test_scan_new_document(self, scanner, tmp_path):
        """Test scanning new document."""
        test_file = tmp_path / "new.txt"
        test_file.write_text("content")
        
        result = await scanner.scan_document(
            document_id=1,
            file_path=str(test_file),
            old_document=None,
        )
        
        assert result.change_type == "new"
        assert result.status == "scanned"
        assert result.file_hash is not None

    @pytest.mark.asyncio
    async def test_scan_unchanged_document(self, scanner, tmp_path):
        """Test scanning unchanged document."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        file_hash = calculate_document_hash(str(test_file))
        old_doc = {
            "file_hash": file_hash,
            "file_size": 7,
            "last_modified": datetime.now().isoformat(),
        }
        
        result = await scanner.scan_document(
            document_id=1,
            file_path=str(test_file),
            old_document=old_doc,
        )
        
        assert result.change_type == "unchanged"

    @pytest.mark.asyncio
    async def test_scan_deleted_document(self, scanner):
        """Test scanning deleted document."""
        result = await scanner.scan_document(
            document_id=1,
            file_path="/nonexistent/file.txt",
            old_document={"file_hash": "abc123"},
        )
        
        assert result.change_type == "deleted"
        assert result.status == "not_found"


# ==================== Synchronizer Tests ====================

class TestIncrementalSynchronizer:
    """Tests for incremental synchronizer."""

    @pytest.fixture
    def synchronizer(self):
        """Create synchronizer instance."""
        return IncrementalSynchronizer()

    @pytest.mark.asyncio
    async def test_synchronize_new_chunks(self, synchronizer):
        """Test synchronizing new chunks."""
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        
        diff = DocumentDiff(
            document_id=1,
            total_chunks=2,
            added_chunks=[
                ChunkDiff(chunk_id=0, operation=DiffOperationType.ADD, new_content="chunk 1", new_hash="hash1", requires_embedding=True),
                ChunkDiff(chunk_id=1, operation=DiffOperationType.ADD, new_content="chunk 2", new_hash="hash2", requires_embedding=True),
            ],
        )
        
        result = await synchronizer.synchronize(
            db_session, 1, diff, {}
        )
        
        assert result.chunks_added == 2
        assert result.success is True

    @pytest.mark.asyncio
    async def test_synchronize_with_removed_chunks(self, synchronizer):
        """Test synchronizing with removed chunks."""
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        
        diff = DocumentDiff(
            document_id=1,
            total_chunks=0,
            removed_chunks=[
                ChunkDiff(chunk_id=0, operation=DiffOperationType.REMOVE, old_content="old", old_hash="hash1"),
            ],
        )
        
        result = await synchronizer.synchronize(
            db_session, 1, diff, {}
        )
        
        assert result.chunks_removed == 1
        assert result.success is True


# ==================== Metadata Tests ====================

class TestMetadataSynchronizer:
    """Tests for metadata synchronizer."""

    @pytest.fixture
    def metadata_sync(self):
        """Create metadata synchronizer instance."""
        return MetadataSynchronizer()

    @pytest.mark.asyncio
    async def test_sync_metadata_changes(self, metadata_sync):
        """Test metadata synchronization with changes."""
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.fetchall = AsyncMock(return_value=[])
        
        old_metadata = {"title": "Old Title", "author": "Alice"}
        new_metadata = {"title": "New Title", "author": "Alice"}
        
        result = await metadata_sync.sync_metadata(
            db_session, 1, old_metadata, new_metadata
        )
        
        assert result.success is True
        assert "title" in result.fields_updated

    @pytest.mark.asyncio
    async def test_sync_metadata_no_changes(self, metadata_sync):
        """Test metadata synchronization with no changes."""
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.fetchall = AsyncMock(return_value=[])
        
        metadata = {"title": "Same Title", "author": "Alice"}
        
        result = await metadata_sync.sync_metadata(
            db_session, 1, metadata, metadata
        )
        
        assert result.success is True
        assert len(result.fields_updated) == 0


# ==================== Tracker Tests ====================

class TestIndexTracker:
    """Tests for index tracker."""

    @pytest.fixture
    def tracker(self):
        """Create tracker instance."""
        return IndexTracker()

    @pytest.mark.asyncio
    async def test_initialize_document(self, tracker, tmp_path):
        """Test initializing document tracking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        
        await tracker.initialize_document(
            db_session, 1, str(test_file), ["chunk 1"]
        )
        
        record = await tracker.get_record(1)
        assert record is not None
        assert record.chunk_count == 1
        assert record.version == 1

    @pytest.mark.asyncio
    async def test_needs_reindex(self, tracker):
        """Test reindex check."""
        # New document needs reindex
        assert await tracker.needs_reindex(1, "hash123") is True
        
        # Initialize record directly in memory
        tracker._records[1] = IndexRecord(
            document_id=1,
            status=IndexStatus.COMPLETED,
            file_hash="hash123",
        )
        
        # Same hash - no reindex needed
        assert await tracker.needs_reindex(1, "hash123") is False
        
        # Different hash - reindex needed
        assert await tracker.needs_reindex(1, "hash456") is True


# ==================== Cleanup Tests ====================

class TestCleanupService:
    """Tests for cleanup service."""

    @pytest.fixture
    def cleanup_service(self):
        """Create cleanup service instance."""
        return CleanupService()

    @pytest.mark.asyncio
    async def test_cleanup_dry_run(self, cleanup_service):
        """Test cleanup in dry run mode."""
        db_session = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        db_session.execute = AsyncMock(return_value=mock_cursor)
        db_session.commit = AsyncMock()
        db_session.fetchall = AsyncMock(return_value=[])
        
        result = await cleanup_service.cleanup(db_session, dry_run=True)
        
        assert result.success is True
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_remove_document_data(self, cleanup_service):
        """Test removing document data."""
        db_session = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(3,))
        db_session.execute = AsyncMock(return_value=mock_cursor)
        db_session.commit = AsyncMock()
        
        result = await cleanup_service.remove_document_data(db_session, 1, dry_run=False)
        
        assert result.success is True
        assert result.deleted_chunks == 3


# ==================== Event Tests ====================

class TestEventManager:
    """Tests for event manager."""

    @pytest.fixture
    def event_manager(self):
        """Create event manager instance."""
        reset_event_manager()
        return get_event_manager()

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_manager):
        """Test event publishing and subscription."""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        event_manager.subscribe(IncrementalEventType.SCAN_COMPLETED, handler)
        
        event = IncrementalEvent(
            event_type=IncrementalEventType.SCAN_COMPLETED,
            document_id=1,
        )
        
        await event_manager.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].document_id == 1

    @pytest.mark.asyncio
    async def test_event_history(self, event_manager):
        """Test event history."""
        event1 = IncrementalEvent(event_type=IncrementalEventType.SCAN_STARTED, document_id=1)
        event2 = IncrementalEvent(event_type=IncrementalEventType.SCAN_COMPLETED, document_id=1)
        
        await event_manager.publish(event1)
        await event_manager.publish(event2)
        
        history = event_manager.get_history(limit=10)
        assert len(history) == 2

    def test_metrics_collector(self):
        """Test metrics collection."""
        collector = MetricsCollector()
        
        event = IncrementalEvent(
            event_type=IncrementalEventType.SCAN_COMPLETED,
            document_id=1,
            duration_seconds=1.5,
        )
        
        collector.record_event(event)
        metrics = collector.get_metrics()
        
        assert metrics["documents_scanned"] == 1
        assert metrics["average_scan_time"] == 1.5


# ==================== Scheduler Tests ====================

class TestScheduler:
    """Tests for scheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance."""
        return IncrementalScheduler()

    @pytest.mark.asyncio
    async def test_add_and_get_task(self, scheduler):
        """Test adding and getting tasks."""
        async def callback():
            pass
        
        task = scheduler.add_task(
            name="Test Task",
            callback=callback,
            interval_seconds=3600,
        )
        
        retrieved = scheduler.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_enable_disable_task(self, scheduler):
        """Test enabling and disabling tasks."""
        async def callback():
            pass
        
        task = scheduler.add_task(
            name="Test Task",
            callback=callback,
            interval_seconds=3600,
        )
        
        assert scheduler.disable_task(task.task_id) is True
        assert scheduler.get_task(task.task_id)["is_active"] is False
        
        assert scheduler.enable_task(task.task_id) is True
        assert scheduler.get_task(task.task_id)["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, scheduler):
        """Test getting all tasks."""
        async def callback1():
            pass
        
        async def callback2():
            pass
        
        scheduler.add_task(name="Task 1", callback=callback1, interval_seconds=3600)
        scheduler.add_task(name="Task 2", callback=callback2, interval_seconds=7200)
        
        tasks = scheduler.get_all_tasks()
        assert len(tasks) == 2


# ==================== Service Tests ====================

class TestIncrementalService:
    """Tests for incremental service."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return IncrementalIndexingService()

    @pytest.mark.asyncio
    async def test_reindex_new_document(self, service, tmp_path):
        """Test reindexing new document."""
        test_file = tmp_path / "new.txt"
        test_file.write_text("test content")
        
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.fetchone = AsyncMock(return_value=None)
        db_session.fetchall = AsyncMock(return_value=[])
        
        job_config = ReindexJobConfig(document_id=1, incremental=True)
        
        result = await service.reindex_document(
            db_session, 1, job_config,
            file_path=str(test_file),
            metadata={"title": "New Doc"},
        )
        
        assert result.change_type == ChangeType.NEW
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scan_all(self, service):
        """Test scanning all documents."""
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.fetchall = AsyncMock(return_value=[
            (1, "/path/to/doc1.txt", "{}"),
            (2, "/path/to/doc2.txt", "{}"),
        ])
        
        with patch.object(service._scanner, 'scan_batch') as mock_scan:
            mock_scan.return_value = [
                ScanResult(document_id=1, file_path="/path/to/doc1.txt", status="unchanged", change_type="unchanged"),
                ScanResult(document_id=2, file_path="/path/to/doc2.txt", status="modified", change_type="modified"),
            ]
            
            result = await service.scan_all(db_session, limit=10)
        
        assert result["total_scanned"] == 2
        assert result["unchanged"] == 1
        assert result["modified"] == 1


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.mark.asyncio
    async def test_full_reindex_pipeline(self, tmp_path):
        """Test complete reindexing pipeline."""
        # Create test file
        test_file = tmp_path / "document.txt"
        test_file.write_text("Original content")
        
        # Initialize service with fresh instance
        service = IncrementalIndexingService()
        
        db_session = Mock()
        db_session.execute = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.fetchall = AsyncMock(return_value=[])
        db_session.fetchone = AsyncMock(return_value=None)
        
        # Step 1: Initial index
        job_config = ReindexJobConfig(document_id=1, incremental=True)
        result1 = await service.reindex_document(
            db_session, 1, job_config,
            file_path=str(test_file),
            metadata={"title": "Document"},
        )
        
        assert result1.change_type == ChangeType.NEW
        assert result1.success is True
        
        # Step 2: Modify document
        test_file.write_text("Modified content")
        
        result2 = await service.reindex_document(
            db_session, 1, job_config,
            file_path=str(test_file),
            metadata={"title": "Document"},
        )
        
        # Both should succeed (second may be NEW since no previous state persisted)
        assert result2.success is True

    @pytest.mark.asyncio
    async def test_incremental_vs_full_reindex(self, tmp_path):
        """Test incremental vs full reindex modes."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("content")
        
        # Test with incremental mode
        config_inc = IncrementalConfig(reindex_mode=IncrementalReindexMode.INCREMENTAL)
        service_inc = IncrementalIndexingService(config_inc)
        
        # Test with full mode
        config_full = IncrementalConfig(reindex_mode=IncrementalReindexMode.FULL)
        service_full = IncrementalIndexingService(config_full)
        
        assert service_inc._config.is_incremental_mode() is True
        assert service_full._config.is_incremental_mode() is False


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_hash_result_data_structure(self):
        """Test HashResult data structure."""
        from app.incremental.hashing import HashResult
        
        result = HashResult(
            document_hash="doc_hash",
            metadata_hash="meta_hash",
            chunk_hashes=["chunk1", "chunk2"],
            vector_hashes=["vec1", "vec2"],
            content_fingerprint="fingerprint",
        )
        
        assert result.document_hash == "doc_hash"
        assert len(result.chunk_hashes) == 2
        assert len(result.vector_hashes) == 2

    def test_document_change_defaults(self):
        """Test DocumentChange default values."""
        change = DocumentChange(document_id=1, change_type=ChangeType.MODIFIED)
        
        assert change.changed_chunks == []
        assert change.unchanged_chunks == []
        assert change.metadata_changed is False
        assert change.requires_vector_regeneration is False

    def test_sync_result_defaults(self):
        """Test SyncResult default values."""
        result = SyncResult(document_id=1, success=True)
        
        assert result.chunks_added == 0
        assert result.chunks_removed == 0
        assert result.embeddings_generated == 0
        assert result.metadata_updated is False

    @pytest.mark.asyncio
    async def test_metadata_tracker_history(self):
        """Test metadata tracker history."""
        tracker = MetadataTracker()
        
        tracker.record_change(1, "title", "Old", "New")
        tracker.record_change(1, "author", "Alice", "Bob")
        
        history = tracker.get_history(1)
        assert len(history) == 2
        assert history[0]["field"] == "title"
        
        tracker.clear_history(1)
        assert len(tracker.get_history(1)) == 0

    @pytest.mark.asyncio
    async def test_file_watcher_state(self):
        """Test file watcher state management."""
        watcher = FileWatcher()
        
        assert watcher.get_state()["running"] is False
        assert len(watcher.get_state()["watched_paths"]) == 0