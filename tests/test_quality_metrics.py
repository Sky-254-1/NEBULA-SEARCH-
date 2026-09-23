"""Tests for quality metrics calculator."""

import pytest
from datetime import datetime

from app.search.quality_metrics import (
    QualityMetricsCalculator,
    UserBehaviorTracker,
    CTRAnalyzer,
    RealTimeAnalytics,
    SearchMetrics,
)


class TestQualityMetricsCalculator:
    """Test QualityMetricsCalculator class."""

    def setup_method(self):
        """Setup for each test."""
        self.calculator = QualityMetricsCalculator()

    def test_precision_at_k(self):
        """Test Precision@K calculation."""
        search = SearchMetrics(
            query="python",
            results=[
                {"id": 1, "title": "Python Guide"},
                {"id": 2, "title": "Java Guide"},
                {"id": 3, "title": "Python Tutorial"},
            ],
            clicked_ids=[1],
            relevant_ids={1, 3},
        )

        # Top 1: 1/1 relevant = 1.0
        assert self.calculator.precision_at_k(search, k=1) == 1.0

        # Top 2: 1/2 relevant = 0.5
        assert self.calculator.precision_at_k(search, k=2) == 0.5

        # Top 3: 2/3 relevant = 0.667
        assert abs(self.calculator.precision_at_k(search, k=3) - 2/3) < 0.01

    def test_precision_at_k_zero(self):
        """Test Precision@K with no results."""
        search = SearchMetrics(
            query="python",
            results=[],
            clicked_ids=[],
            relevant_ids={1, 2},
        )
        assert self.calculator.precision_at_k(search, k=10) == 0.0

    def test_recall_at_k(self):
        """Test Recall@K calculation."""
        search = SearchMetrics(
            query="python",
            results=[
                {"id": 1, "title": "Python Guide"},
                {"id": 2, "title": "Java Guide"},
                {"id": 3, "title": "Python Tutorial"},
            ],
            clicked_ids=[1],
            relevant_ids={1, 3},
        )

        # Top 1: 1/2 relevant = 0.5
        assert self.calculator.recall_at_k(search, k=1) == 0.5

        # Top 2: 1/2 relevant = 0.5
        assert self.calculator.recall_at_k(search, k=2) == 0.5

        # Top 3: 2/2 relevant = 1.0
        assert self.calculator.recall_at_k(search, k=3) == 1.0

    def test_recall_at_k_no_relevant(self):
        """Test Recall@K with no relevant documents."""
        search = SearchMetrics(
            query="python",
            results=[{"id": 1, "title": "Python"}],
            clicked_ids=[],
            relevant_ids=set(),
        )
        assert self.calculator.recall_at_k(search, k=10) == 0.0

    def test_mean_reciprocal_rank(self):
        """Test MRR calculation."""
        # First relevant at position 1
        search1 = SearchMetrics(
            query="python",
            results=[
                {"id": 1},
                {"id": 2},
            ],
            clicked_ids=[],
            relevant_ids={1},
        )
        assert self.calculator.mean_reciprocal_rank(search1) == 1.0

        # First relevant at position 2
        search2 = SearchMetrics(
            query="python",
            results=[
                {"id": 2},
                {"id": 1},
            ],
            clicked_ids=[],
            relevant_ids={1},
        )
        assert self.calculator.mean_reciprocal_rank(search2) == 0.5

        # No relevant
        search3 = SearchMetrics(
            query="python",
            results=[{"id": 1}, {"id": 2}],
            clicked_ids=[],
            relevant_ids=set(),
        )
        assert self.calculator.mean_reciprocal_rank(search3) == 0.0

    def test_ndcg_at_k(self):
        """Test NDCG@K calculation."""
        # Perfect ranking
        search1 = SearchMetrics(
            query="python",
            results=[
                {"id": 1},
                {"id": 2},
                {"id": 3},
            ],
            clicked_ids=[],
            relevant_ids={1, 2, 3},
        )
        assert abs(self.calculator.ndcg_at_k(search1, k=3) - 1.0) < 0.01

        # Imperfect ranking - only 2 out of 3 are relevant
        search2 = SearchMetrics(
            query="python",
            results=[
                {"id": 3},
                {"id": 1},
                {"id": 2},
            ],
            clicked_ids=[],
            relevant_ids={1, 2},
        )
        assert 0 < self.calculator.ndcg_at_k(search2, k=3) < 1.0

    def test_ndcg_at_k_no_relevant(self):
        """Test NDCG@K with no relevant documents."""
        search = SearchMetrics(
            query="python",
            results=[{"id": 1}],
            clicked_ids=[],
            relevant_ids=set(),
        )
        assert self.calculator.ndcg_at_k(search, k=10) == 0.0

    def test_calculate_metrics(self):
        """Test calculating all metrics."""
        search = SearchMetrics(
            query="python",
            results=[
                {"id": 1},
                {"id": 2},
                {"id": 3},
            ],
            clicked_ids=[],
            relevant_ids={1, 3},
        )

        metrics = self.calculator.calculate_metrics(search, k=3)

        assert 'precision@3' in metrics
        assert 'recall@3' in metrics
        assert 'mrr' in metrics
        assert 'ndcg@3' in metrics
        assert all(0 <= v <= 1 for v in metrics.values())

    def test_get_average_metrics(self):
        """Test getting average metrics."""
        # No metrics yet
        avg = self.calculator.get_average_metrics(hours=24)
        assert avg['precision@10'] == 0.0
        assert avg['mrr'] == 0.0


class TestUserBehaviorTracker:
    """Test UserBehaviorTracker class."""

    def setup_method(self):
        """Setup for each test."""
        self.tracker = UserBehaviorTracker()

    def test_track_click(self):
        """Test tracking click events."""
        timestamp = datetime.now()
        self.tracker.track_click(1, "python", 123, 1, timestamp)

        events = self.tracker.realtime_events
        assert len(events) == 1
        assert events[0]['type'] == 'click'
        assert events[0]['user_id'] == 1
        assert events[0]['result_id'] == 123

    def test_track_search(self):
        """Test tracking search events."""
        timestamp = datetime.now()
        self.tracker.track_search(1, "python", 10, "hybrid", timestamp)

        events = self.tracker.realtime_events
        assert len(events) == 1
        assert events[0]['type'] == 'search'
        assert events[0]['result_count'] == 10

    def test_track_dwell_time(self):
        """Test tracking dwell time."""
        timestamp = datetime.now()
        self.tracker.track_dwell_time(1, 123, 5.5, timestamp)

        events = self.tracker.realtime_events
        assert len(events) == 1
        assert events[0]['type'] == 'dwell'
        assert events[0]['dwell_seconds'] == 5.5

    def test_get_click_through_rate(self):
        """Test CTR calculation."""
        timestamp = datetime.now()
        self.tracker.track_search(1, "python", 10, "hybrid", timestamp)
        self.tracker.track_click(1, "python", 1, 1, timestamp)
        self.tracker.track_click(1, "python", 2, 2, timestamp)

        ctr = self.tracker.get_click_through_rate("python")
        assert ctr == 2.0 / 1.0  # 2 clicks, 1 search

    def test_get_click_through_rate_no_searches(self):
        """Test CTR with no searches."""
        ctr = self.tracker.get_click_through_rate("python")
        assert ctr == 0.0

    def test_get_average_rank(self):
        """Test average rank calculation."""
        timestamp = datetime.now()
        self.tracker.track_click(1, "python", 1, 1, timestamp)
        self.tracker.track_click(1, "python", 2, 3, timestamp)
        self.tracker.track_click(1, "python", 3, 5, timestamp)

        avg_rank = self.tracker.get_average_rank("python")
        assert avg_rank == (1 + 3 + 5) / 3

    def test_get_recent_events(self):
        """Test getting recent events."""
        timestamp = datetime.now()
        self.tracker.track_click(1, "python", 1, 1, timestamp)

        recent = self.tracker.get_recent_events(minutes=5)
        assert len(recent) == 1


class TestCTRAnalyzer:
    """Test CTRAnalyzer class."""

    def setup_method(self):
        """Setup for each test."""
        self.analyzer = CTRAnalyzer()

    def test_record_ctr(self):
        """Test recording CTR."""
        self.analyzer.record_ctr(1, 0.5)
        self.analyzer.record_ctr(1, 0.6)

        assert self.analyzer.calculate_position_ctr(1) == 0.55

    def test_calculate_position_ctr_no_data(self):
        """Test CTR calculation with no data."""
        assert self.analyzer.calculate_position_ctr(1) == 0.0

    def test_get_ctr_distribution(self):
        """Test getting CTR distribution."""
        self.analyzer.record_ctr(1, 0.5)
        self.analyzer.record_ctr(2, 0.3)

        distribution = self.analyzer.get_ctr_distribution()
        assert distribution[1] == 0.5
        assert distribution[2] == 0.3
        assert distribution[3] == 0.0

    def test_analyze_query_ctr(self):
        """Test analyzing query CTR."""
        events = [
            {'type': 'search', 'user_id': 1},
            {'type': 'search', 'user_id': 1},
            {'type': 'click', 'user_id': 1},
        ]

        ctr = self.analyzer.analyze_query_ctr("python", events)
        assert ctr == 0.5

    def test_get_top_queries_by_ctr(self):
        """Test getting top queries by CTR."""
        self.analyzer.ctr_by_query = {
            'python': 0.8,
            'java': 0.6,
            'javascript': 0.9,
        }

        top = self.analyzer.get_top_queries_by_ctr(limit=2)
        assert len(top) == 2
        assert top[0][0] == 'javascript'
        assert top[0][1] == 0.9


class TestRealTimeAnalytics:
    """Test RealTimeAnalytics class."""

    def setup_method(self):
        """Setup for each test."""
        self.analytics = RealTimeAnalytics()

    def test_record_search(self):
        """Test recording search."""
        self.analytics.record_search(1, "python", 10, 100.0)

        assert self.analytics.total_searches == 1
        assert len(self.analytics.queries_per_minute) == 1
        assert len(self.analytics.latency_samples) == 1

    def test_record_click(self):
        """Test recording click."""
        self.analytics.record_click(1, "python", 123, 1)

        assert self.analytics.total_clicks == 1

    def test_record_evaluation(self):
        """Test recording evaluation."""
        search = SearchMetrics(
            query="python",
            results=[{"id": 1}],
            clicked_ids=[],
            relevant_ids={1},
        )

        metrics = self.analytics.record_evaluation(search)
        assert 'precision@10' in metrics
        assert 'recall@10' in metrics
        assert 'mrr' in metrics
        assert 'ndcg@10' in metrics

    def test_get_dashboard_stats(self):
        """Test getting dashboard stats."""
        self.analytics.record_search(1, "python", 10, 100.0)
        self.analytics.record_click(1, "python", 1, 1)

        stats = self.analytics.get_dashboard_stats()

        assert stats['total_searches'] == 1
        assert stats['total_clicks'] == 1
        assert 'queries_per_minute' in stats
        assert 'avg_latency_ms' in stats
        assert 'avg_precision@10' in stats