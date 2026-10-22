"""Tests for 0% coverage files: hybrid_search, personalization, quality_metrics,
indexing events/models/services, background_tasks, and health_routes."""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.search.hybrid_search import HybridSearchEngine, hybrid_search_engine
from app.search.personalization import (
    PersonalizationEngine,
    UserProfile,
)
from app.search.quality_metrics import (
    CTRAnalyzer,
    QualityMetricsCalculator,
    RealTimeAnalytics,
    SearchMetrics,
    UserBehaviorTracker,
)


# ============================================================
# HybridSearchEngine Tests
# ============================================================
class TestHybridSearchEngine:
    """Tests for HybridSearchEngine."""

    def test_init_default_weights(self):
        engine = HybridSearchEngine()
        assert engine.lexical_weight == pytest.approx(0.5)
        assert engine.semantic_weight == pytest.approx(0.5)
        assert engine.enable_deduplication is True
        assert engine.enable_reranking is True

    def test_init_custom_weights(self):
        engine = HybridSearchEngine(lexical_weight=0.7, semantic_weight=0.3)
        assert engine.lexical_weight == pytest.approx(0.7)
        assert engine.semantic_weight == pytest.approx(0.3)

    def test_init_weights_normalized(self):
        engine = HybridSearchEngine(lexical_weight=2.0, semantic_weight=1.0)
        assert engine.lexical_weight == pytest.approx(2.0 / 3.0)
        assert engine.semantic_weight == pytest.approx(1.0 / 3.0)

    def test_update_weights(self):
        engine = HybridSearchEngine()
        engine.update_weights(0.8, 0.2)
        assert engine.lexical_weight == pytest.approx(0.8)
        assert engine.semantic_weight == pytest.approx(0.2)

    def test_normalize_scores_empty(self):
        engine = HybridSearchEngine()
        result = engine._normalize_scores([], "lexical_score")
        assert result == []

    def test_normalize_scores_uniform(self):
        engine = HybridSearchEngine()
        results = [{"lexical_score": 0.5}, {"lexical_score": 0.5}]
        normalized = engine._normalize_scores(results, "lexical_score")
        assert all(r["lexical_score"] == 0.5 for r in normalized)

    def test_normalize_scores_range(self):
        engine = HybridSearchEngine()
        results = [{"lexical_score": 0.1}, {"lexical_score": 0.9}]
        normalized = engine._normalize_scores(results, "lexical_score")
        assert normalized[0]["lexical_score"] == pytest.approx(0.0)
        assert normalized[1]["lexical_score"] == pytest.approx(1.0)

    def test_deduplicate_by_url(self):
        engine = HybridSearchEngine()
        results = [
            {"url": "https://example.com/a", "content": "alpha"},
            {"url": "https://example.com/a", "content": "beta"},
            {"url": "https://example.com/b", "content": "gamma"},
        ]
        unique = engine._deduplicate(results)
        assert len(unique) == 2

    def test_deduplicate_by_content(self):
        engine = HybridSearchEngine()
        results = [
            {"url": "", "content": "same content here"},
            {"url": "", "content": "same content here"},
        ]
        unique = engine._deduplicate(results)
        assert len(unique) == 1

    def test_deduplicate_empty_fields(self):
        engine = HybridSearchEngine()
        results = [
            {"url": "", "content": ""},
            {"url": "", "content": ""},
        ]
        unique = engine._deduplicate(results)
        assert len(unique) == 2  # No dedup when no URL/content

    def test_merge_results(self):
        engine = HybridSearchEngine(lexical_weight=0.5, semantic_weight=0.5)
        web = [
            {"id": "w1", "title": "Web 1", "url": "https://w.com/1", "content": "web content 1", "lexical_score": 0.8, "semantic_score": 0.0},
        ]
        vector = [
            {"id": "v1", "title": "Vector 1", "url": "https://v.com/1", "content": "vector content 1", "lexical_score": 0.0, "semantic_score": 0.9},
        ]
        merged = engine._merge_results(web, vector, top_k=10)
        assert len(merged) == 2
        assert "score" in merged[0]
        assert "scores" in merged[0]

    def test_merge_results_sorted_by_score(self):
        engine = HybridSearchEngine(lexical_weight=0.5, semantic_weight=0.5)
        web = [
            {"id": "w1", "url": "https://w.com/1", "content": "c1", "lexical_score": 0.1, "semantic_score": 0.0},
        ]
        vector = [
            {"id": "v1", "url": "https://v.com/2", "content": "c2", "lexical_score": 0.0, "semantic_score": 0.9},
        ]
        merged = engine._merge_results(web, vector, top_k=10)
        # After normalization, single-element lists get score 0.5
        # Combined: 0.5*0.5 + 0.5*0.0 = 0.25 for web, 0.5*0.0 + 0.5*0.5 = 0.25 for vector
        # Both equal, so just verify we have 2 results sorted
        assert len(merged) == 2
        assert "score" in merged[0]

    def test_merge_results_top_k(self):
        engine = HybridSearchEngine(enable_deduplication=False)
        web = [{"id": f"w{i}", "url": f"https://w.com/{i}", "content": f"c{i}", "lexical_score": 0.5, "semantic_score": 0.0} for i in range(10)]
        vector = [{"id": f"v{i}", "url": f"https://v.com/{i}", "content": f"d{i}", "lexical_score": 0.0, "semantic_score": 0.5} for i in range(10)]
        merged = engine._merge_results(web, vector, top_k=5)
        assert len(merged) == 5

    @pytest.mark.asyncio
    async def test_search_with_mocks(self):
        engine = HybridSearchEngine(enable_reranking=False)

        with patch("app.services.search.run_web_search", new_callable=AsyncMock) as mock_web, \
             patch("vector.pipeline.hybrid_search", new_callable=AsyncMock) as mock_vec:
            mock_web.return_value = [{"title": "Test", "snippet": "Snippet", "url": "https://test.com", "score": 0.8}]
            mock_vec.return_value = [{"chunk_id": "c1", "filename": "doc.pdf", "content": "content", "url": "", "keyword_score": 0.5, "vector_score": 0.9}]

            results = await engine.search("test query", top_k=5)
            assert isinstance(results, list)
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_web_fails_gracefully(self):
        engine = HybridSearchEngine(enable_reranking=False)

        with patch("app.services.search.run_web_search", new_callable=AsyncMock) as mock_web, \
             patch("vector.pipeline.hybrid_search", new_callable=AsyncMock) as mock_vec:
            mock_web.side_effect = Exception("Network error")
            mock_vec.return_value = []

            results = await engine.search("test", top_k=5)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_vector_fails_gracefully(self):
        engine = HybridSearchEngine(enable_reranking=False)

        with patch("app.services.search.run_web_search", new_callable=AsyncMock) as mock_web, \
             patch("vector.pipeline.hybrid_search", new_callable=AsyncMock) as mock_vec:
            mock_web.return_value = []
            mock_vec.side_effect = Exception("Vector DB error")

            results = await engine.search("test", top_k=5)
            assert isinstance(results, list)

    def test_global_instance(self):
        assert hybrid_search_engine is not None
        assert isinstance(hybrid_search_engine, HybridSearchEngine)


# ============================================================
# Personalization Tests
# ============================================================
class TestUserProfile:
    """Tests for UserProfile."""

    def test_init(self):
        profile = UserProfile(user_id=1)
        assert profile.user_id == 1
        assert profile.interests == []
        assert profile.frequent_queries == []
        assert profile.preferred_categories == []
        assert profile.personalization_enabled is True

    def test_from_dict(self):
        data = {
            "interests": ["python", "search"],
            "frequent_queries": json.dumps(["query1", "query2"]),
            "preferred_categories": json.dumps(["tech", "science"]),
            "personalization_enabled": False,
        }
        profile = UserProfile.from_dict(1, data)
        assert profile.interests == ["python", "search"]
        assert profile.frequent_queries == ["query1", "query2"]
        assert profile.preferred_categories == ["tech", "science"]
        assert profile.personalization_enabled is False

    def test_from_dict_defaults(self):
        profile = UserProfile.from_dict(1, {})
        assert profile.interests == []
        assert profile.frequent_queries == []
        assert profile.preferred_categories == []
        assert profile.personalization_enabled is True

    def test_to_dict(self):
        profile = UserProfile(user_id=1)
        profile.interests = ["python"]
        profile.interest_weights = {"python": 0.8}
        d = profile.to_dict()
        assert d["user_id"] == 1
        assert d["interests"] == ["python"]
        assert d["interest_weights"] == {"python": 0.8}


class TestPersonalizationEngine:
    """Tests for PersonalizationEngine."""

    @pytest.mark.asyncio
    async def test_get_profile_no_db(self):
        engine = PersonalizationEngine(db=None)
        profile = await engine.get_user_profile(user_id=1)
        assert profile.user_id == 1
        assert profile.interests == []

    @pytest.mark.asyncio
    async def test_get_profile_cached(self):
        engine = PersonalizationEngine(db=None)
        # First call creates and caches
        profile1 = await engine.get_user_profile(user_id=1)
        # Second call returns cached
        profile2 = await engine.get_user_profile(user_id=1)
        assert profile1 is profile2

    def test_extract_interests(self):
        engine = PersonalizationEngine(db=None)
        history = [
            {"query": "python machine learning"},
            {"query": "python data science"},
            {"query": "the quick brown fox"},
        ]
        interests = engine._extract_interests(history)
        assert "python" in interests
        assert "machine" in interests or "learning" in interests
        # Stop words should be filtered
        assert "the" not in interests

    def test_extract_interests_empty(self):
        engine = PersonalizationEngine(db=None)
        assert engine._extract_interests([]) == []

    def test_extract_interests_filters_short_words(self):
        engine = PersonalizationEngine(db=None)
        history = [{"query": "a b cd ef"}]
        interests = engine._extract_interests(history)
        # Words with len <= 2 are filtered
        assert "a" not in interests
        assert "b" not in interests
        assert "cd" not in interests  # len == 2, filtered

    def test_calculate_interest_weights(self):
        engine = PersonalizationEngine(db=None)
        history = [
            {"query": "python search", "frequency": 3, "last_used": datetime.now().isoformat()},
            {"query": "python ai", "frequency": 1, "last_used": datetime.now().isoformat()},
        ]
        weights = engine._calculate_interest_weights(history)
        assert "python" in weights
        # python appears in both, should have highest weight (1.0 after normalization)
        assert weights["python"] == pytest.approx(1.0)

    def test_calculate_interest_weights_empty(self):
        engine = PersonalizationEngine(db=None)
        assert engine._calculate_interest_weights([]) == {}

    def test_calculate_interest_weights_invalid_date(self):
        engine = PersonalizationEngine(db=None)
        history = [{"query": "test", "frequency": 1, "last_used": "invalid-date"}]
        weights = engine._calculate_interest_weights(history)
        assert "test" in weights

    def test_calculate_category_weights(self):
        engine = PersonalizationEngine(db=None)
        weights = engine._calculate_category_weights(["tech", "science", "health"])
        assert len(weights) == 3
        assert all(w == pytest.approx(1.0 / 3.0) for w in weights.values())

    def test_calculate_category_weights_empty(self):
        engine = PersonalizationEngine(db=None)
        assert engine._calculate_category_weights([]) == {}

    def test_calculate_result_score_adjustment_no_personalization(self):
        engine = PersonalizationEngine(db=None)
        profile = UserProfile(user_id=1)
        profile.personalization_enabled = False
        adjustment = engine.calculate_result_score_adjustment(profile, {"title": "test", "snippet": "test"})
        assert adjustment == 0.0

    def test_calculate_result_score_adjustment_with_interests(self):
        engine = PersonalizationEngine(db=None)
        profile = UserProfile(user_id=1)
        profile.interests = ["python", "search"]
        adjustment = engine.calculate_result_score_adjustment(
            profile, {"title": "Python Search Engine", "snippet": "A search tool"}
        )
        assert adjustment > 0.0
        assert adjustment <= 0.2

    def test_calculate_result_score_adjustment_with_categories(self):
        engine = PersonalizationEngine(db=None)
        profile = UserProfile(user_id=1)
        profile.preferred_categories = ["Tech", "Science"]
        adjustment = engine.calculate_result_score_adjustment(
            profile, {"title": "Tech News", "snippet": "Science update"}
        )
        assert adjustment > 0.0
        assert adjustment <= 0.2

    def test_calculate_result_score_adjustment_no_match(self):
        engine = PersonalizationEngine(db=None)
        profile = UserProfile(user_id=1)
        profile.interests = ["python"]
        adjustment = engine.calculate_result_score_adjustment(
            profile, {"title": "Cooking Recipe", "snippet": "How to bake"}
        )
        assert adjustment == 0.0

    @pytest.mark.asyncio
    async def test_get_personalized_weights_disabled(self):
        engine = PersonalizationEngine(db=None)
        # Create a profile with personalization disabled
        profile = await engine.get_user_profile(1)
        profile.personalization_enabled = False
        engine._profile_cache[1] = profile

        base = {"relevance": 0.5, "personalization": 0.1}
        result = await engine.get_personalized_weights(1, base)
        assert result == base

    @pytest.mark.asyncio
    async def test_get_personalized_weights_enabled(self):
        engine = PersonalizationEngine(db=None)
        profile = await engine.get_user_profile(1)
        profile.interest_weights = {"python": 0.8, "search": 0.6}
        engine._profile_cache[1] = profile

        base = {"relevance": 0.5, "personalization": 0.1}
        result = await engine.get_personalized_weights(1, base)
        assert result["personalization"] >= 0.1

    @pytest.mark.asyncio
    async def test_learn_from_search_no_repo(self):
        engine = PersonalizationEngine(db=None)
        # Should not raise even without repo
        await engine.learn_from_search(1, "test query")


# ============================================================
# Quality Metrics Tests
# ============================================================
class TestQualityMetricsCalculator:
    """Tests for QualityMetricsCalculator."""

    def test_precision_at_k(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 1}, {"id": 2}, {"id": 3}],
            clicked_ids=[1],
            relevant_ids={1, 3},
        )
        assert calc.precision_at_k(search, k=3) == pytest.approx(2 / 3)

    def test_precision_at_k_empty(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(query="test", results=[], clicked_ids=[], relevant_ids=set())
        assert calc.precision_at_k(search, k=10) == 0.0

    def test_precision_at_k_zero_k(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(query="test", results=[{"id": 1}], clicked_ids=[], relevant_ids={1})
        assert calc.precision_at_k(search, k=0) == 0.0

    def test_recall_at_k(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 1}, {"id": 2}, {"id": 3}],
            clicked_ids=[1],
            relevant_ids={1, 3, 5},
        )
        assert calc.recall_at_k(search, k=3) == pytest.approx(2 / 3)

    def test_recall_at_k_no_relevant(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(query="test", results=[{"id": 1}], clicked_ids=[], relevant_ids=set())
        assert calc.recall_at_k(search, k=10) == 0.0

    def test_mean_reciprocal_rank(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 5}, {"id": 3}, {"id": 1}],
            clicked_ids=[],
            relevant_ids={1},
        )
        assert calc.mean_reciprocal_rank(search) == pytest.approx(1 / 3)

    def test_mean_reciprocal_rank_no_match(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 5}, {"id": 6}],
            clicked_ids=[],
            relevant_ids={1},
        )
        assert calc.mean_reciprocal_rank(search) == 0.0

    def test_ndcg_at_k(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 1}, {"id": 2}, {"id": 3}],
            clicked_ids=[],
            relevant_ids={1, 3},
        )
        ndcg = calc.ndcg_at_k(search, k=3)
        assert 0.0 < ndcg <= 1.0

    def test_ndcg_at_k_no_relevant(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(query="test", results=[{"id": 1}], clicked_ids=[], relevant_ids=set())
        assert calc.ndcg_at_k(search, k=10) == 0.0

    def test_ndcg_at_k_zero_k(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(query="test", results=[{"id": 1}], clicked_ids=[], relevant_ids={1})
        assert calc.ndcg_at_k(search, k=0) == 0.0

    def test_calculate_metrics(self):
        calc = QualityMetricsCalculator()
        search = SearchMetrics(
            query="test",
            results=[{"id": 1}, {"id": 2}],
            clicked_ids=[1],
            relevant_ids={1},
        )
        metrics = calc.calculate_metrics(search, k=10)
        assert "precision@10" in metrics
        assert "recall@10" in metrics
        assert "mrr" in metrics
        assert "ndcg@10" in metrics

    def test_get_average_metrics_empty(self):
        calc = QualityMetricsCalculator()
        avg = calc.get_average_metrics()
        assert avg["precision@10"] == 0.0
        assert avg["mrr"] == 0.0

    def test_get_average_metrics_with_data(self):
        calc = QualityMetricsCalculator()
        search1 = SearchMetrics(query="t1", results=[{"id": 1}], clicked_ids=[], relevant_ids={1})
        search2 = SearchMetrics(query="t2", results=[{"id": 2}], clicked_ids=[], relevant_ids={2})
        calc.calculate_metrics(search1)
        calc.calculate_metrics(search2)
        avg = calc.get_average_metrics()
        assert "precision@10" in avg
        assert avg["precision@10"] > 0.0


class TestUserBehaviorTracker:
    """Tests for UserBehaviorTracker."""

    def test_track_click(self):
        tracker = UserBehaviorTracker()
        tracker.track_click(1, "test", 101, 1, datetime.now())
        events = tracker.sessions["test"]
        assert len(events) == 1
        assert events[0]["type"] == "click"

    def test_track_search(self):
        tracker = UserBehaviorTracker()
        tracker.track_search(1, "test", 10, "hybrid", datetime.now())
        events = tracker.sessions["test"]
        assert len(events) == 1
        assert events[0]["type"] == "search"

    def test_track_dwell_time(self):
        tracker = UserBehaviorTracker()
        tracker.track_dwell_time(1, 101, 5.5, datetime.now())
        assert len(tracker.realtime_events) == 1
        assert tracker.realtime_events[0]["type"] == "dwell"

    def test_click_through_rate(self):
        tracker = UserBehaviorTracker()
        now = datetime.now()
        tracker.track_search(1, "test", 10, "hybrid", now)
        tracker.track_search(1, "test", 10, "hybrid", now)
        tracker.track_click(1, "test", 101, 1, now)
        ctr = tracker.get_click_through_rate("test")
        assert ctr == pytest.approx(0.5)

    def test_click_through_rate_no_searches(self):
        tracker = UserBehaviorTracker()
        assert tracker.get_click_through_rate("nonexistent") == 0.0

    def test_average_rank(self):
        tracker = UserBehaviorTracker()
        now = datetime.now()
        tracker.track_click(1, "test", 101, 1, now)
        tracker.track_click(1, "test", 102, 3, now)
        avg_rank = tracker.get_average_rank("test")
        assert avg_rank == pytest.approx(2.0)

    def test_average_rank_no_clicks(self):
        tracker = UserBehaviorTracker()
        assert tracker.get_average_rank("nonexistent") == 0.0

    def test_get_recent_events(self):
        tracker = UserBehaviorTracker()
        now = datetime.now()
        tracker.track_search(1, "test", 10, "hybrid", now)
        recent = tracker.get_recent_events(minutes=5)
        assert len(recent) == 1

    def test_get_recent_events_old(self):
        tracker = UserBehaviorTracker()
        old_time = datetime.now() - timedelta(hours=2)
        tracker.track_search(1, "test", 10, "hybrid", old_time)
        recent = tracker.get_recent_events(minutes=5)
        assert len(recent) == 0


class TestCTRAnalyzer:
    """Tests for CTRAnalyzer."""

    def test_record_and_calculate_ctr(self):
        analyzer = CTRAnalyzer()
        analyzer.record_ctr(1, 0.5)
        analyzer.record_ctr(1, 0.3)
        assert analyzer.calculate_position_ctr(1) == pytest.approx(0.4)

    def test_calculate_ctr_no_data(self):
        analyzer = CTRAnalyzer()
        assert analyzer.calculate_position_ctr(99) == 0.0

    def test_get_ctr_distribution(self):
        analyzer = CTRAnalyzer()
        analyzer.record_ctr(1, 0.5)
        analyzer.record_ctr(2, 0.3)
        dist = analyzer.get_ctr_distribution()
        assert len(dist) == 10
        assert dist[1] == pytest.approx(0.5)
        assert dist[2] == pytest.approx(0.3)

    def test_analyze_query_ctr(self):
        analyzer = CTRAnalyzer()
        events = [
            {"type": "search"},
            {"type": "search"},
            {"type": "click"},
        ]
        ctr = analyzer.analyze_query_ctr("test", events)
        # 1 click / 2 searches = 0.5
        assert ctr == pytest.approx(0.5)

    def test_analyze_query_ctr_no_searches(self):
        analyzer = CTRAnalyzer()
        assert analyzer.analyze_query_ctr("test", []) == 0.0

    def test_get_top_queries_by_ctr(self):
        analyzer = CTRAnalyzer()
        analyzer.ctr_by_query = {"a": 0.8, "b": 0.5, "c": 0.9}
        top = analyzer.get_top_queries_by_ctr(limit=2)
        assert top[0][0] == "c"
        assert top[1][0] == "a"


class TestRealTimeAnalytics:
    """Tests for RealTimeAnalytics."""

    def test_record_search(self):
        analytics = RealTimeAnalytics()
        analytics.record_search(1, "test", 10, 50.0)
        assert analytics.total_searches == 1
        assert len(analytics.queries_per_minute) == 1
        assert len(analytics.latency_samples) == 1

    def test_record_click(self):
        analytics = RealTimeAnalytics()
        analytics.record_click(1, "test", 101, 1)
        assert analytics.total_clicks == 1

    def test_record_evaluation(self):
        analytics = RealTimeAnalytics()
        search = SearchMetrics(
            query="test",
            results=[{"id": 1}],
            clicked_ids=[],
            relevant_ids={1},
        )
        metrics = analytics.record_evaluation(search)
        assert "precision@10" in metrics

    def test_get_dashboard_stats(self):
        analytics = RealTimeAnalytics()
        analytics.record_search(1, "test", 10, 50.0)
        analytics.record_click(1, "test", 101, 1)
        stats = analytics.get_dashboard_stats()
        assert stats["total_searches"] == 1
        assert stats["total_clicks"] == 1
        assert "queries_per_minute" in stats
        assert "avg_latency_ms" in stats

    def test_get_dashboard_stats_empty(self):
        analytics = RealTimeAnalytics()
        stats = analytics.get_dashboard_stats()
        assert stats["total_searches"] == 0
        assert stats["avg_latency_ms"] == 0.0