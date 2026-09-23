"""Metrics collection for indexing system."""

import logging
import time
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger("nebula.indexing.metrics")


@dataclass
class MetricSnapshot:
    """Snapshot of indexing metrics."""
    timestamp: float
    indexed_documents: int = 0
    queue_length: int = 0
    average_indexing_time: float = 0.0
    worker_utilization: float = 0.0
    embedding_speed: float = 0.0
    chunks_indexed: int = 0
    failures: int = 0
    retries: int = 0
    cancelled_jobs: int = 0
    storage_throughput: float = 0.0


class MetricsCollector:
    """Collects and tracks indexing metrics."""
    
    def __init__(self, max_history: int = 1000) -> None:
        self._indexed_documents = 0
        self._failures = 0
        self._retries = 0
        self._cancelled_jobs = 0
        self._chunks_indexed = 0
        self._total_indexing_time = 0.0
        self._recent_durations: deque[float] = deque(maxlen=100)
        self._start_time = time.time()
        self._history: deque[MetricSnapshot] = deque(maxlen=max_history)
        self._lock = None
    
    def record_indexed_document(self, duration: float, chunks: int = 0) -> None:
        """Record a successfully indexed document."""
        self._indexed_documents += 1
        self._total_indexing_time += duration
        self._chunks_indexed += chunks
        self._recent_durations.append(duration)
        logger.debug("Recorded indexed document (duration=%.2f, chunks=%d)", duration, chunks)
    
    def record_failure(self) -> None:
        """Record a failed indexing job."""
        self._failures += 1
        logger.debug("Recorded indexing failure")
    
    def record_retry(self) -> None:
        """Record a retry attempt."""
        self._retries += 1
        logger.debug("Recorded retry")
    
    def record_cancellation(self) -> None:
        """Record a cancelled job."""
        self._cancelled_jobs += 1
        logger.debug("Recorded cancellation")
    
    def get_metrics(self) -> dict:
        """
        Get current metrics.
        
        Returns:
            Dictionary with all metrics
        """
        avg_time = 0.0
        if self._recent_durations:
            avg_time = sum(self._recent_durations) / len(self._recent_durations)
        
        uptime = time.time() - self._start_time
        docs_per_second = self._indexed_documents / uptime if uptime > 0 else 0
        
        return {
            "indexed_documents": self._indexed_documents,
            "queue_length": 0,  # Updated externally
            "average_indexing_time": round(avg_time, 2),
            "worker_utilization": 0.0,  # Updated externally
            "embedding_speed": docs_per_second,
            "chunks_indexed": self._chunks_indexed,
            "failures": self._failures,
            "retries": self._retries,
            "cancelled_jobs": self._cancelled_jobs,
            "storage_throughput": 0.0,  # Updated externally
            "uptime_seconds": round(uptime, 2),
        }
    
    def get_detailed_metrics(self) -> dict:
        """
        Get detailed metrics with percentiles.
        
        Returns:
            Dictionary with detailed metrics
        """
        metrics = self.get_metrics()
        
        if self._recent_durations:
            sorted_durations = sorted(self._recent_durations)
            n = len(sorted_durations)
            metrics["p50_indexing_time"] = sorted_durations[n // 2]
            metrics["p95_indexing_time"] = sorted_durations[int(n * 0.95)]
            metrics["p99_indexing_time"] = sorted_durations[int(n * 0.99)]
            metrics["max_indexing_time"] = sorted_durations[-1]
            metrics["min_indexing_time"] = sorted_durations[0]
        
        return metrics
    
    def take_snapshot(self) -> MetricSnapshot:
        """Take a snapshot of current metrics for historical tracking."""
        return MetricSnapshot(
            timestamp=time.time(),
            indexed_documents=self._indexed_documents,
            queue_length=0,  # Updated via property
            average_indexing_time=self.get_metrics()["average_indexing_time"],
            failures=self._failures,
            retries=self._retries,
            cancelled_jobs=self._cancelled_jobs,
            chunks_indexed=self._chunks_indexed,
        )
    
    def update_queue_length(self, length: int) -> None:
        """Update queue length metric."""
        if self._history:
            self._history[-1].queue_length = length
    
    def update_worker_utilization(self, utilization: float) -> None:
        """Update worker utilization metric."""
        if self._history:
            self._history[-1].worker_utilization = utilization
    
    def update_storage_throughput(self, throughput: float) -> None:
        """Update storage throughput metric."""
        if self._history:
            self._history[-1].storage_throughput = throughput
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._indexed_documents = 0
        self._failures = 0
        self._retries = 0
        self._cancelled_jobs = 0
        self._chunks_indexed = 0
        self._total_indexing_time = 0.0
        self._recent_durations.clear()
        self._start_time = time.time()
        logger.info("Metrics reset")


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return metrics_collector