"""Quality metrics calculator for search evaluation.

Implements:
- Precision@K, Recall, MRR, NDCG
- User behavior tracking
- Click-through rate analysis
- Real-time analytics
"""

import logging
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("nebula.search.metrics")


@dataclass
class SearchMetrics:
    """Metrics for a single search session."""
    query: str
    results: list[dict]
    clicked_ids: list[int]
    relevant_ids: set[int]
    timestamp: datetime = field(default_factory=datetime.now)


class QualityMetricsCalculator:
    """Calculate search quality metrics."""

    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)

    def precision_at_k(self, search: SearchMetrics, k: int = 10) -> float:
        """Calculate Precision@K."""
        if k == 0 or not search.results:
            return 0.0

        top_k = search.results[:k]
        relevant_in_top_k = sum(1 for r in top_k if r.get('id') in search.relevant_ids)
        return relevant_in_top_k / k

    def recall_at_k(self, search: SearchMetrics, k: int = 10) -> float:
        """Calculate Recall@K."""
        if not search.relevant_ids:
            return 0.0

        top_k = search.results[:k]
        relevant_in_top_k = sum(1 for r in top_k if r.get('id') in search.relevant_ids)
        return relevant_in_top_k / len(search.relevant_ids)

    def mean_reciprocal_rank(self, search: SearchMetrics) -> float:
        """Calculate Mean Reciprocal Rank (MRR)."""
        for idx, result in enumerate(search.results, 1):
            if result.get('id') in search.relevant_ids:
                return 1.0 / idx
        return 0.0

    def ndcg_at_k(self, search: SearchMetrics, k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain at K."""
        if not search.relevant_ids or k == 0:
            return 0.0

        dcg = 0.0
        for idx, result in enumerate(search.results[:k], 1):
            if result.get('id') in search.relevant_ids:
                dcg += 1.0 / math.log2(idx + 1)

        idcg = 0.0
        num_relevant = min(len(search.relevant_ids), k)
        for idx in range(1, num_relevant + 1):
            idcg += 1.0 / math.log2(idx + 1)

        return dcg / idcg if idcg > 0 else 0.0

    def calculate_metrics(self, search: SearchMetrics, k: int = 10) -> dict[str, float]:
        """Calculate all metrics for a search session."""
        metrics = {
            f'precision@{k}': self.precision_at_k(search, k),
            f'recall@{k}': self.recall_at_k(search, k),
            'mrr': self.mean_reciprocal_rank(search),
            f'ndcg@{k}': self.ndcg_at_k(search, k),
        }

        self.metrics_history.append(metrics)

        logger.debug(
            "Metrics for query '%s': P@%d=%.3f, R@%d=%.3f, MRR=%.3f, NDCG@%d=%.3f",
            search.query, k, metrics[f'precision@{k}'], k, metrics[f'recall@{k}'],
            metrics['mrr'], k, metrics[f'ndcg@{k}'],
        )

        return metrics

    def get_average_metrics(self, hours: int = 24) -> dict[str, float]:
        """Get average metrics over time window."""
        recent = list(self.metrics_history)[-100:]

        if not recent:
            return {
                'precision@10': 0.0,
                'recall@10': 0.0,
                'mrr': 0.0,
                'ndcg@10': 0.0,
            }

        avg_metrics = defaultdict(list)
        for metrics in recent:
            for key, value in metrics.items():
                avg_metrics[key].append(value)

        return {key: sum(values) / len(values) for key, values in avg_metrics.items()}


class UserBehaviorTracker:
    """Track user behavior for analytics."""

    def __init__(self):
        self.sessions: dict[str, list[dict]] = defaultdict(list)
        self.realtime_events: deque = deque(maxlen=1000)

    def track_click(
        self, user_id: int, query: str, result_id: int, rank: int, timestamp: datetime
    ) -> None:
        """Track a click event."""
        event = {
            'user_id': user_id,
            'query': query,
            'result_id': result_id,
            'rank': rank,
            'timestamp': timestamp.isoformat(),
            'type': 'click',
        }

        self.sessions[query].append(event)
        self.realtime_events.append(event)

    def track_search(
        self,
        user_id: int,
        query: str,
        result_count: int,
        search_type: str,
        timestamp: datetime,
    ) -> None:
        """Track a search event."""
        event = {
            'user_id': user_id,
            'query': query,
            'result_count': result_count,
            'search_type': search_type,
            'timestamp': timestamp.isoformat(),
            'type': 'search',
        }

        self.sessions[query].append(event)
        self.realtime_events.append(event)

    def track_dwell_time(
        self, user_id: int, result_id: int, dwell_seconds: float, timestamp: datetime
    ) -> None:
        """Track time spent on a result."""
        event = {
            'user_id': user_id,
            'result_id': result_id,
            'dwell_seconds': dwell_seconds,
            'timestamp': timestamp.isoformat(),
            'type': 'dwell',
        }

        self.realtime_events.append(event)

    def get_click_through_rate(self, query: str) -> float:
        """Calculate click-through rate for a query."""
        events = self.sessions.get(query, [])

        searches = sum(1 for e in events if e['type'] == 'search')
        clicks = sum(1 for e in events if e['type'] == 'click')

        return clicks / searches if searches > 0 else 0.0

    def get_average_rank(self, query: str) -> float:
        """Get average rank of clicked results for a query."""
        events = self.sessions.get(query, [])
        clicks = [e for e in events if e['type'] == 'click']

        if not clicks:
            return 0.0

        ranks = [e['rank'] for e in clicks]
        return sum(ranks) / len(ranks)

    def get_recent_events(self, minutes: int = 5) -> list[dict]:
        """Get recent events for real-time analytics."""
        cutoff = datetime.now() - timedelta(minutes=minutes)

        return [
            event for event in self.realtime_events
            if datetime.fromisoformat(event['timestamp']) >= cutoff
        ]


class CTRAnalyzer:
    """Analyze click-through rate patterns."""

    def __init__(self):
        self.ctr_by_position: dict[int, list[float]] = defaultdict(list)
        self.ctr_by_query: dict[str, float] = {}

    def record_ctr(self, position: int, ctr: float) -> None:
        """Record CTR for a position."""
        self.ctr_by_position[position].append(ctr)

    def calculate_position_ctr(self, position: int) -> float:
        """Calculate average CTR for a position."""
        ctrs = self.ctr_by_position.get(position, [])
        return sum(ctrs) / len(ctrs) if ctrs else 0.0

    def get_ctr_distribution(self) -> dict[int, float]:
        """Get CTR distribution across positions."""
        return {
            pos: self.calculate_position_ctr(pos)
            for pos in range(1, 11)
        }

    def analyze_query_ctr(self, query: str, events: list[dict]) -> float:
        """Analyze CTR for a specific query."""
        searches = sum(1 for e in events if e['type'] == 'search')
        clicks = sum(1 for e in events if e['type'] == 'click')

        if searches == 0:
            return 0.0

        ctr = clicks / searches
        self.ctr_by_query[query] = ctr

        return ctr

    def get_top_queries_by_ctr(self, limit: int = 10) -> list[tuple[str, float]]:
        """Get top queries by CTR."""
        sorted_queries = sorted(
            self.ctr_by_query.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]


class RealTimeAnalytics:
    """Real-time analytics dashboard data."""

    def __init__(self):
        self.metrics_calculator = QualityMetricsCalculator()
        self.behavior_tracker = UserBehaviorTracker()
        self.ctr_analyzer = CTRAnalyzer()
        self.total_searches = 0
        self.total_clicks = 0
        self.queries_per_minute: deque = deque(maxlen=60)
        self.latency_samples: deque = deque(maxlen=1000)

    def record_search(self, user_id: int, query: str, result_count: int, latency_ms: float) -> None:
        """Record a search event."""
        self.total_searches += 1
        timestamp = datetime.now()
        self.behavior_tracker.track_search(user_id, query, result_count, 'hybrid', timestamp)

        self.queries_per_minute.append(timestamp)
        self.latency_samples.append(latency_ms)

    def record_click(self, user_id: int, query: str, result_id: int, rank: int) -> None:
        """Record a click event."""
        self.total_clicks += 1
        self.behavior_tracker.track_click(user_id, query, result_id, rank, datetime.now())

    def record_evaluation(self, search: SearchMetrics) -> dict[str, float]:
        """Record search evaluation metrics."""
        return self.metrics_calculator.calculate_metrics(search, k=10)

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Get real-time dashboard statistics."""
        recent_events = self.behavior_tracker.get_recent_events(minutes=1)

        one_minute_ago = datetime.now() - timedelta(minutes=1)
        qpm = sum(
            1 for ts in self.queries_per_minute
            if ts >= one_minute_ago
        )

        avg_latency = (
            sum(self.latency_samples) / len(self.latency_samples)
            if self.latency_samples
            else 0.0
        )

        avg_metrics = self.metrics_calculator.get_average_metrics(hours=1)

        return {
            'total_searches': self.total_searches,
            'total_clicks': self.total_clicks,
            'queries_per_minute': qpm,
            'avg_latency_ms': avg_latency,
            'recent_events_count': len(recent_events),
            'avg_precision@10': avg_metrics.get('precision@10', 0.0),
            'avg_recall@10': avg_metrics.get('recall@10', 0.0),
            'avg_mrr': avg_metrics.get('mrr', 0.0),
            'avg_ndcg@10': avg_metrics.get('ndcg@10', 0.0),
        }