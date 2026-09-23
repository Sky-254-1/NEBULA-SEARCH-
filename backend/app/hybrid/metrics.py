"""
Hybrid Search Metrics

Collects and tracks performance and quality metrics for hybrid search.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.hybrid.metrics")


@dataclass
class SearchMetrics:
    """Metrics for a single search operation"""
    query: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Timing
    total_latency_ms: float = 0.0
    bm25_latency_ms: float = 0.0
    vector_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    deduplication_latency_ms: float = 0.0
    
    # Results
    result_count: int = 0
    bm25_result_count: int = 0
    vector_result_count: int = 0
    duplicates_removed: int = 0
    
    # Scores
    average_score: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0
    
    # Intent
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    
    # System
    success: bool = True
    error: Optional[str] = None


class HybridMetrics:
    """
    Track hybrid search metrics.
    
    Metrics:
    - Latency (total, bm25, vector, fusion, dedup)
    - Result counts
    - Score distributions
    - Success rates
    - Common queries
    - Intent distribution
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of search records to keep
        """
        self.max_history = max_history
        self.searches: deque = deque(maxlen=max_history)
        
        # Aggregated metrics
        self.total_searches = 0
        self.successful_searches = 0
        self.failed_searches = 0
        
        # Timing aggregates
        self.total_latency_sum = 0.0
        self.bm25_latency_sum = 0.0
        self.vector_latency_sum = 0.0
        self.fusion_latency_sum = 0.0
        self.dedup_latency_sum = 0.0
        
        # Score aggregates
        self.score_sum = 0.0
        self.score_count = 0
        
        # Result count aggregates
        self.result_count_sum = 0
        self.duplicates_removed_sum = 0
        
        # Query tracking
        self.query_counts = defaultdict(int)
        self.recent_queries: deque = deque(maxlen=100)
        
        # Intent tracking
        self.intent_counts = defaultdict(int)
        
        # Error tracking
        self.error_counts = defaultdict(int)
        
        # Time-based metrics
        self.hourly_searches = defaultdict(int)
        self.daily_searches = defaultdict(int)

    def record_search(self, metrics: SearchMetrics):
        """
        Record metrics for a search operation.
        
        Args:
            metrics: Search metrics to record
        """
        self.searches.append(metrics)
        self.total_searches += 1
        
        # Update success/failure counts
        if metrics.success:
            self.successful_searches += 1
        else:
            self.failed_searches += 1
            if metrics.error:
                self.error_counts[metrics.error] += 1
        
        # Update timing aggregates
        self.total_latency_sum += metrics.total_latency_ms
        self.bm25_latency_sum += metrics.bm25_latency_ms
        self.vector_latency_sum += metrics.vector_latency_ms
        self.fusion_latency_sum += metrics.fusion_latency_ms
        self.dedup_latency_sum += metrics.deduplication_latency_ms
        
        # Update score aggregates
        if metrics.result_count > 0:
            self.score_sum += metrics.average_score * metrics.result_count
            self.score_count += metrics.result_count
        
        # Update result aggregates
        self.result_count_sum += metrics.result_count
        self.duplicates_removed_sum += metrics.duplicates_removed
        
        # Track query
        self.query_counts[metrics.query] += 1
        self.recent_queries.append(metrics.query)
        
        # Track intent
        if metrics.intent:
            self.intent_counts[metrics.intent] += 1
        
        # Track time-based metrics
        hour_key = metrics.timestamp.strftime("%Y-%m-%d %H:00")
        day_key = metrics.timestamp.strftime("%Y-%m-%d")
        self.hourly_searches[hour_key] += 1
        self.daily_searches[day_key] += 1

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Returns:
            Summary dictionary
        """
        if self.total_searches == 0:
            return {
                "total_searches": 0,
                "success_rate": 0.0,
                "average_latency_ms": 0.0,
            }
        
        # Calculate averages
        avg_latency = self.total_latency_sum / self.total_searches
        avg_bm25_latency = self.bm25_latency_sum / self.total_searches
        avg_vector_latency = self.vector_latency_sum / self.total_searches
        avg_fusion_latency = self.fusion_latency_sum / self.total_searches
        avg_dedup_latency = self.dedup_latency_sum / self.total_searches
        
        avg_result_count = self.result_count_sum / self.total_searches
        avg_score = self.score_sum / self.score_count if self.score_count > 0 else 0.0
        
        success_rate = self.successful_searches / self.total_searches
        
        return {
            "total_searches": self.total_searches,
            "successful_searches": self.successful_searches,
            "failed_searches": self.failed_searches,
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "latency_breakdown": {
                "bm25_avg_ms": avg_bm25_latency,
                "vector_avg_ms": avg_vector_latency,
                "fusion_avg_ms": avg_fusion_latency,
                "dedup_avg_ms": avg_dedup_latency,
            },
            "average_result_count": avg_result_count,
            "total_duplicates_removed": self.duplicates_removed_sum,
            "average_score": avg_score,
            "top_queries": self.get_top_queries(10),
            "recent_queries": list(self.recent_queries)[-20:],
            "intent_distribution": dict(self.intent_counts),
            "error_distribution": dict(self.error_counts),
            "hourly_searches": dict(self.hourly_searches),
            "daily_searches": dict(self.daily_searches),
        }

    def get_top_queries(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N most common queries.
        
        Args:
            n: Number of queries to return
            
        Returns:
            List of top queries with counts
        """
        sorted_queries = sorted(
            self.query_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return [
            {"query": query, "count": count}
            for query, count in sorted_queries[:n]
        ]

    def get_no_result_queries(self) -> List[str]:
        """Get queries that returned no results"""
        no_result = []
        
        for metrics in self.searches:
            if metrics.result_count == 0:
                no_result.append(metrics.query)
        
        return no_result

    def get_percentiles(self, metric: str = "total_latency_ms") -> Dict[str, float]:
        """
        Calculate percentiles for a metric.
        
        Args:
            metric: Metric name
            
        Returns:
            Percentiles (p50, p95, p99)
        """
        if not self.searches:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        values = [getattr(m, metric, 0.0) for m in self.searches]
        values.sort()
        
        n = len(values)
        p50_idx = int(n * 0.5)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        
        return {
            "p50": values[p50_idx] if values else 0.0,
            "p95": values[p95_idx] if p95_idx < n else 0.0,
            "p99": values[p99_idx] if p99_idx < n else 0.0,
        }

    def get_recent_performance(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get performance metrics for recent time window.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Performance metrics
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent = [m for m in self.searches if m.timestamp >= cutoff]
        
        if not recent:
            return {
                "window_minutes": minutes,
                "search_count": 0,
                "average_latency_ms": 0.0,
            }
        
        latencies = [m.total_latency_ms for m in recent]
        avg_latency = sum(latencies) / len(latencies)
        
        return {
            "window_minutes": minutes,
            "search_count": len(recent),
            "average_latency_ms": avg_latency,
            "success_rate": sum(1 for m in recent if m.success) / len(recent),
            "average_result_count": sum(m.result_count for m in recent) / len(recent),
        }

    def reset(self):
        """Reset all metrics"""
        self.searches.clear()
        self.total_searches = 0
        self.successful_searches = 0
        self.failed_searches = 0
        self.total_latency_sum = 0.0
        self.bm25_latency_sum = 0.0
        self.vector_latency_sum = 0.0
        self.fusion_latency_sum = 0.0
        self.dedup_latency_sum = 0.0
        self.score_sum = 0.0
        self.score_count = 0
        self.result_count_sum = 0
        self.duplicates_removed_sum = 0
        self.query_counts.clear()
        self.recent_queries.clear()
        self.intent_counts.clear()
        self.error_counts.clear()
        self.hourly_searches.clear()
        self.daily_searches.clear()

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for monitoring/analytics.
        
        Returns:
            Complete metrics dictionary
        """
        return {
            "summary": self.get_summary(),
            "percentiles": {
                "latency": self.get_percentiles("total_latency_ms"),
                "bm25_latency": self.get_percentiles("bm25_latency_ms"),
                "vector_latency": self.get_percentiles("vector_latency_ms"),
                "score": self.get_percentiles("average_score"),
            },
            "recent_performance_5m": self.get_recent_performance(5),
            "recent_performance_1h": self.get_recent_performance(60),
        }