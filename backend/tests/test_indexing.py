"""Comprehensive tests for the indexing system."""

import asyncio
import logging
from pathlib import Path

import pytest

from app.indexing.config import JobPriority, JobStatus, get_indexing_config
from app.indexing.deadletter import DeadLetterQueue
from app.indexing.health import WorkerHealthMonitor
from app.indexing.metrics import MetricsCollector
from app.indexing.progress import ProgressTracker
from app.indexing.queue import IndexingQueue
from app.indexing.retry import RetryHandler, RetryPolicy
from app.indexing.scheduler import IndexingScheduler, ScheduleType
from app.indexing.tasks import chunk_text, calculate_file_checksum, detect_file_type
from app.indexing.worker import Worker

logger = logging.getLogger("nebula.indexing.tests")


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------


class TestConfig:
    """Test indexing configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = get_indexing_config()
        assert config.max_queue_size > 0
        assert config.worker_count > 0
        assert config.max_retries > 0
        assert config.retry_base_delay > 0

    def test_priority_values(self) -> None:
        """Test job priority enum."""
        assert JobPriority.SYSTEM.value == "SYSTEM"
        assert JobPriority.HIGH.value == "HIGH"
        assert JobPriority.NORMAL.value == "NORMAL"
        assert JobPriority.LOW.value == "LOW"


# ---------------------------------------------------------------------------
# Queue tests
# ---------------------------------------------------------------------------


class TestQueue:
    """Test priority queue functionality."""

    @pytest.fixture
    async def queue(self) -> IndexingQueue:
        """Create a fresh queue instance."""
        q = IndexingQueue()
        await q.connect()
        yield q
        await q.clear()
        await q.close()

    async def test_enqueue_dequeue(self, queue: IndexingQueue) -> None:
        """Test basic enqueue and dequeue."""
        job = {"job_id": "test-1", "type": "index", "priority": JobPriority.NORMAL}
        await queue.enqueue(job)
        assert queue.size == 1

        result = await queue.dequeue()
        assert result is not None
        assert result["job_id"] == "test-1"
        assert queue.size == 0

    async def test_priority_ordering(self, queue: IndexingQueue) -> None:
        """Test that higher priority jobs are dequeued first."""
        low_job = {"job_id": "low", "type": "index", "priority": JobPriority.LOW}
        high_job = {"job_id": "high", "type": "index", "priority": JobPriority.HIGH}
        normal_job = {"job_id": "normal", "type": "index", "priority": JobPriority.NORMAL}

        await queue.enqueue(low_job)
        await queue.enqueue(high_job)
        await queue.enqueue(normal_job)

        # Should dequeue in priority order: HIGH, NORMAL, LOW
        first = await queue.dequeue()
        assert first["job_id"] == "high"

        second = await queue.dequeue()
        assert second["job_id"] == "normal"

        third = await queue.dequeue()
        assert third["job_id"] == "low"

    async def test_peek(self, queue: IndexingQueue) -> None:
        """Test peeking at queue without removing."""
        job1 = {"job_id": "1", "type": "index", "priority": JobPriority.NORMAL}
        job2 = {"job_id": "2", "type": "index", "priority": JobPriority.HIGH}

        await queue.enqueue(job1)
        await queue.enqueue(job2)

        peeked = await queue.peek(count=10)
        assert len(peeked) == 2
        assert queue.size == 2  # Queue should not be modified

    async def test_remove(self, queue: IndexingQueue) -> None:
        """Test removing specific job from queue."""
        job1 = {"job_id": "remove-me", "type": "index"}
        job2 = {"job_id": "keep-me", "type": "index"}

        await queue.enqueue(job1)
        await queue.enqueue(job2)

        result = await queue.remove("remove-me")
        assert result is True
        assert queue.size == 1

        result = await queue.remove("nonexistent")
        assert result is False

    async def test_pause_resume(self, queue: IndexingQueue) -> None:
        """Test pausing and resuming queue."""
        assert not queue.is_paused

        queue.pause()
        assert queue.is_paused

        queue.resume()
        assert not queue.is_paused

    async def test_clear(self, queue: IndexingQueue) -> None:
        """Test clearing queue."""
        await queue.enqueue({"job_id": "1", "type": "index"})
        await queue.enqueue({"job_id": "2", "type": "index"})
        assert queue.size == 2

        await queue.clear()
        assert queue.size == 0
        assert queue.is_empty


# ---------------------------------------------------------------------------
# Progress tests
# ---------------------------------------------------------------------------


class TestProgress:
    """Test progress tracking."""

    @pytest.fixture
    def tracker(self) -> ProgressTracker:
        """Create a fresh progress tracker."""
        return ProgressTracker()

    def test_create_progress(self, tracker: ProgressTracker) -> None:
        """Test creating progress for a job."""
        progress = tracker.create("job-1")
        assert progress.job_id == "job-1"
        assert progress.status == "QUEUED"
        assert progress.progress == 0

    def test_update_status(self, tracker: ProgressTracker) -> None:
        """Test updating job status."""
        tracker.create("job-1")
        tracker.update_status("job-1", JobStatus.RUNNING)
        progress = tracker.get("job-1")
        assert progress.status == "RUNNING"

    def test_update_step(self, tracker: ProgressTracker) -> None:
        """Test updating job step."""
        tracker.create("job-1")
        progress = tracker.get("job-1")
        progress.update_step("CHUNKING", 30)
        assert progress.progress == 30

    def test_complete_job(self, tracker: ProgressTracker) -> None:
        """Test marking job as complete."""
        tracker.create("job-1")
        tracker.start("job-1", "worker-1")
        tracker.complete("job-1")
        progress = tracker.get("job-1")
        assert progress.status == "COMPLETED"
        assert progress.progress == 100

    def test_fail_job(self, tracker: ProgressTracker) -> None:
        """Test marking job as failed."""
        tracker.create("job-1")
        tracker.fail("job-1", "Test error")
        progress = tracker.get("job-1")
        assert progress.status == "FAILED"
        assert progress.error_message == "Test error"

    def test_cancel_job(self, tracker: ProgressTracker) -> None:
        """Test cancelling a job."""
        tracker.create("job-1")
        tracker.cancel("job-1")
        progress = tracker.get("job-1")
        assert progress.status == "CANCELLED"

    def test_speed_calculation(self, tracker: ProgressTracker) -> None:
        """Test speed calculation."""
        tracker.create("job-1", document_size=1000)
        tracker.start("job-1", "worker-1")
        
        progress = tracker.get("job-1")
        progress.chunks_processed = 10
        
        speed = progress.speed
        assert speed is not None
        assert "chunks/sec" in speed

    def test_eta_calculation(self, tracker: ProgressTracker) -> None:
        """Test ETA calculation."""
        tracker.create("job-1")
        tracker.start("job-1", "worker-1")
        
        progress = tracker.get("job-1")
        progress.progress = 50
        
        eta = progress.eta_seconds
        assert eta is not None
        assert eta > 0


# ---------------------------------------------------------------------------
# Retry tests
# ---------------------------------------------------------------------------


class TestRetry:
    """Test retry logic."""

    @pytest.fixture
    def retry_handler(self) -> RetryHandler:
        """Create retry handler with test configuration."""
        policy = RetryPolicy(max_retries=3, base_delay=0.1, backoff_multiplier=3.0)
        return RetryHandler(policy)

    def test_should_retry_transient_error(self, retry_handler: RetryHandler) -> None:
        """Test that transient errors should be retried."""
        error = ConnectionError("Network timeout")
        assert retry_handler.should_retry(error, 0) is True

    def test_should_not_retry_non_retryable(self, retry_handler: RetryHandler) -> None:
        """Test that non-retryable errors should not be retried."""
        error = ValueError("Unsupported file")
        assert retry_handler.should_retry(error, 0) is False

    def test_should_not_retry_after_max(self, retry_handler: RetryHandler) -> None:
        """Test that jobs are not retried after max retries."""
        error = ConnectionError("Network error")
        assert retry_handler.should_retry(error, 3) is False

    def test_exponential_backoff(self, retry_handler: RetryHandler) -> None:
        """Test exponential backoff delays."""
        delay_0 = retry_handler.get_delay(0)
        delay_1 = retry_handler.get_delay(1)
        delay_2 = retry_handler.get_delay(2)

        assert delay_1 > delay_0
        assert delay_2 > delay_1

    def test_execute_with_retry_success(self, retry_handler: RetryHandler) -> None:
        """Test successful execution without retries."""
        call_count = 0

        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = asyncio.run(retry_handler.execute_with_retry(successful_func))
        assert result == "success"
        assert call_count == 1

    def test_execute_with_retry_eventual_success(self, retry_handler: RetryHandler) -> None:
        """Test retry that eventually succeeds."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        # Need to mock time.sleep for this test
        original_sleep = asyncio.sleep
        async def mock_sleep(duration):
            pass
        
        asyncio.sleep = mock_sleep
        try:
            result = asyncio.run(retry_handler.execute_with_retry(failing_func))
            assert result == "success"
            assert call_count == 3
        finally:
            asyncio.sleep = original_sleep


# ---------------------------------------------------------------------------
# Dead-letter queue tests
# ---------------------------------------------------------------------------


class TestDeadLetterQueue:
    """Test dead-letter queue."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        class MockDB:
            async def execute(self, sql, params=()):
                return MockCursor()
        
        class MockCursor:
            def __init__(self):
                self.rowcount = 1
            
            async def fetchone(self):
                return {"count": 0}
            
            async def fetchall(self):
                return []
        
        return MockDB()

    async def test_add_job(self, mock_db) -> None:
        """Test adding job to dead-letter queue."""
        dlq = DeadLetterQueue(mock_db)
        await dlq.add(
            job_id="job-1",
            document_id=1,
            filename="test.pdf",
            failure_reason="Test error",
            retries=5,
        )

    async def test_list_jobs(self, mock_db) -> None:
        """Test listing dead-letter queue."""
        dlq = DeadLetterQueue(mock_db)
        jobs = await dlq.list_all()
        assert isinstance(jobs, list)

    async def test_count(self, mock_db) -> None:
        """Test counting dead-letter queue."""
        dlq = DeadLetterQueue(mock_db)
        count = await dlq.count()
        assert isinstance(count, int)


# ---------------------------------------------------------------------------
# Health monitoring tests
# ---------------------------------------------------------------------------


class TestHealthMonitor:
    """Test worker health monitoring."""

    @pytest.fixture
    def monitor(self) -> WorkerHealthMonitor:
        """Create fresh health monitor."""
        return WorkerHealthMonitor()

    def test_register_worker(self, monitor: WorkerHealthMonitor) -> None:
        """Test worker registration."""
        worker_id = monitor.register_worker()
        assert worker_id is not None
        assert worker_id in monitor.get_all_workers()

    def test_unregister_worker(self, monitor: WorkerHealthMonitor) -> None:
        """Test worker unregistration."""
        worker_id = monitor.register_worker()
        monitor.unregister_worker(worker_id)
        worker = monitor.get_worker(worker_id)
        assert worker.status == "STOPPED"

    def test_heartbeat(self, monitor: WorkerHealthMonitor) -> None:
        """Test worker heartbeat."""
        worker_id = monitor.register_worker()
        monitor.heartbeat(worker_id)
        worker = monitor.get_worker(worker_id)
        assert worker.last_heartbeat > 0

    def test_update_status(self, monitor: WorkerHealthMonitor) -> None:
        """Test updating worker status."""
        worker_id = monitor.register_worker()
        monitor.update_status(worker_id, "BUSY", "job-1")
        worker = monitor.get_worker(worker_id)
        assert worker.status == "BUSY"
        assert worker.current_job_id == "job-1"

    def test_record_completion(self, monitor: WorkerHealthMonitor) -> None:
        """Test recording job completion."""
        worker_id = monitor.register_worker()
        monitor.record_job_completion(worker_id, 2.5, success=True)
        worker = monitor.get_worker(worker_id)
        assert worker.processed_jobs == 1
        assert worker.average_duration == 2.5

    def test_get_statistics(self, monitor: WorkerHealthMonitor) -> None:
        """Test getting worker statistics."""
        monitor.register_worker()
        stats = monitor.get_statistics()
        assert stats["total_workers"] == 1
        assert stats["active_workers"] == 1


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------


class TestMetrics:
    """Test metrics collection."""

    @pytest.fixture
    def metrics(self) -> MetricsCollector:
        """Create fresh metrics collector."""
        return MetricsCollector()

    def test_record_indexed_document(self, metrics: MetricsCollector) -> None:
        """Test recording indexed document."""
        metrics.record_indexed_document(2.5, chunks=10)
        m = metrics.get_metrics()
        assert m["indexed_documents"] == 1
        assert m["chunks_indexed"] == 10

    def test_record_failure(self, metrics: MetricsCollector) -> None:
        """Test recording failure."""
        metrics.record_failure()
        m = metrics.get_metrics()
        assert m["failures"] == 1

    def test_record_retry(self, metrics: MetricsCollector) -> None:
        """Test recording retry."""
        metrics.record_retry()
        m = metrics.get_metrics()
        assert m["retries"] == 1

    def test_record_cancellation(self, metrics: MetricsCollector) -> None:
        """Test recording cancellation."""
        metrics.record_cancellation()
        m = metrics.get_metrics()
        assert m["cancelled_jobs"] == 1

    def test_avg_indexing_time(self, metrics: MetricsCollector) -> None:
        """Test average indexing time calculation."""
        metrics.record_indexed_document(2.0, chunks=5)
        metrics.record_indexed_document(4.0, chunks=5)
        m = metrics.get_metrics()
        assert m["average_indexing_time"] == 3.0

    def test_reset(self, metrics: MetricsCollector) -> None:
        """Test resetting metrics."""
        metrics.record_indexed_document(2.0)
        metrics.record_failure()
        metrics.reset()

        m = metrics.get_metrics()
        assert m["indexed_documents"] == 0
        assert m["failures"] == 0


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------


class TestScheduler:
    """Test scheduler functionality."""

    @pytest.fixture
    def scheduler(self) -> IndexingScheduler:
        """Create fresh scheduler."""
        return IndexingScheduler()

    def test_register_task(self, scheduler: IndexingScheduler) -> None:
        """Test registering a task."""
        async def dummy_task():
            pass

        config = scheduler.register_task(
            name="test-task",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=3600,
            callback=dummy_task,
        )
        assert config.name == "test-task"
        assert config.next_run is not None

    def test_get_task_status(self, scheduler: IndexingScheduler) -> None:
        """Test getting task status."""
        scheduler.register_task(
            name="test-task",
            schedule_type=ScheduleType.MANUAL,
        )
        status = scheduler.get_task_status("test-task")
        assert status is not None
        assert status["name"] == "test-task"

    def test_get_all_tasks(self, scheduler: IndexingScheduler) -> None:
        """Test getting all tasks."""
        scheduler.register_task("task-1", ScheduleType.MANUAL)
        scheduler.register_task("task-2", ScheduleType.MANUAL)
        tasks = scheduler.get_all_tasks()
        assert len(tasks) == 2


# ---------------------------------------------------------------------------
# Worker tests
# ---------------------------------------------------------------------------


class TestWorker:
    """Test worker functionality."""

    def test_worker_creation(self) -> None:
        """Test creating a worker."""
        worker = Worker()
        assert worker.worker_id is not None

    async def test_worker_start_stop(self) -> None:
        """Test starting and stopping a worker."""
        worker = Worker()
        await worker.start()
        assert worker._running is True
        
        await worker.stop()
        assert worker._running is False

    async def test_worker_run_once_empty_queue(self) -> None:
        """Test worker with empty queue."""
        worker = Worker()
        await worker.start()
        await worker.run_once()  # Should not raise
        await worker.stop()


# ---------------------------------------------------------------------------
# Task helper tests
# ---------------------------------------------------------------------------


class TestTaskHelpers:
    """Test task helper functions."""

    def test_chunk_text(self) -> None:
        """Test text chunking."""
        text = "This is a test. " * 100
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 60  # Allow some overflow for word boundaries

    def test_chunk_empty_text(self) -> None:
        """Test chunking empty text."""
        chunks = chunk_text("")
        assert chunks == []

    def test_detect_file_type(self) -> None:
        """Test file type detection."""
        assert detect_file_type("test.pdf") == "pdf"
        assert detect_file_type("test.txt") == "text"
        assert detect_file_type("test.html") == "html"
        assert detect_file_type("test.unknown") == "unknown"

    def test_calculate_file_checksum(self, tmp_path: Path) -> None:
        """Test file checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum1 = calculate_file_checksum(str(test_file))
        checksum2 = calculate_file_checksum(str(test_file))
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIndexingIntegration:
    """Integration tests for the indexing system."""

    async def test_full_indexing_flow(self) -> None:
        """Test complete indexing workflow."""
        # This would require a full database setup
        # Placeholder for integration test
        pass

    async def test_queue_persistence(self) -> None:
        """Test that jobs survive restarts (simulated)."""
        # Would test Redis persistence
        pass

    async def test_cancellation(self) -> None:
        """Test job cancellation."""
        # Would test cancelling a running job
        pass