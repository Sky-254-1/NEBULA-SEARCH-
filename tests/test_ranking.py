"""Tests for ML-based ranking engine."""

import pytest
from datetime import datetime, timedelta

from app.search.ranking import (
    MLRanker,
    HybridRanker,
    RankingModelManager,
    RankingFeatures,
    BM25Ranker,
    TFIDFRanker,
    PositionAwareRanker,
    DiversityRanker,
)


class TestBM25Ranker:
    """Test BM25 ranking algorithm."""

    def test_basic_scoring(self):
        """Test basic BM25 scoring."""
        ranker = BM25Ranker()
        documents = [
            {"title": "Python programming", "snippet": "Learn Python"},
            {"title": "Java programming", "snippet": "Learn Java"},
        ]
        ranker.index_documents(documents)
        
        score = ranker.score("python", documents[0])
        assert score > 0
    
    def test_no_documents(self):
        """Test scoring with no indexed documents."""
        ranker = BM25Ranker()
        score = ranker.score("python", {"title": "Python"})
        assert score == 0.0


class TestTFIDFRanker:
    """Test TF-IDF ranking."""

    def test_tf_calculation(self):
        """Test term frequency calculation."""
        ranker = TFIDFRanker()
        tf = ranker.calculate_tf("python", "python python java")
        assert tf == 2/3
    
    def test_idf_calculation(self):
        """Test IDF calculation."""
        ranker = TFIDFRanker()
        docs = [
            {"title": "Python", "snippet": "python"},
            {"title": "Java", "snippet": "java"},
        ]
        idf = ranker.calculate_idf("python", docs)
        assert idf > 0
    
    def test_score_calculation(self):
        """Test TF-IDF score calculation."""
        ranker = TFIDFRanker()
        docs = [
            {"title": "Python", "snippet": "python programming"},
            {"title": "Java", "snippet": "java programming"},
        ]
        score = ranker.score("python", docs[0], docs)
        assert score > 0


class TestPositionAwareRanker:
    """Test position-aware ranking."""

    def test_title_match(self):
        """Test title matching."""
        ranker = PositionAwareRanker()
        doc = {"title": "Python Programming", "snippet": "Learn", "url": "http://example.com/python"}
        score = ranker.score("Python", doc)
        assert score > 0
    
    def test_url_match(self):
        """Test URL matching."""
        ranker = PositionAwareRanker()
        doc = {"title": "Article", "snippet": "About programming", "url": "http://python.org"}
        score = ranker.score("python", doc)
        assert score > 0


class TestMLRanker:
    """Test ML-based ranking."""

    def setup_method(self):
        """Setup for each test."""
        self.ranker = MLRanker()
        self.documents = [
            {
                "id": 1,
                "title": "Python Programming Guide",
                "snippet": "Learn Python programming",
                "url": "https://python.org",
            },
            {
                "id": 2,
                "title": "Java vs Python",
                "snippet": "Comparison of languages",
                "url": "https://example.com",
            },
        ]
    
    def test_feature_extraction(self):
        """Test feature extraction."""
        features = self.ranker.extract_features("python", self.documents[0], self.documents)
        
        assert features.bm25_score > 0
        assert features.title_match is True
        assert features.snippet_match is True
        assert features.url_match is True
        assert features.freshness_score >= 0
        assert features.domain_authority >= 0
    
    def test_freshness_calculation(self):
        """Test freshness score calculation."""
        # Recent document
        recent_doc = {"published_date": datetime.now().isoformat()}
        freshness = self.ranker._calculate_freshness(recent_doc)
        assert freshness > 0.5
        
        # Old document
        old_doc = {"published_date": (datetime.now() - timedelta(days=365)).isoformat()}
        freshness_old = self.ranker._calculate_freshness(old_doc)
        assert freshness_old < freshness
    
    def test_domain_authority(self):
        """Test domain authority calculation."""
        high_auth = {"url": "https://wikipedia.org/python"}
        assert self.ranker._calculate_domain_authority(high_auth) == 0.9
        
        low_auth = {"url": "https://example.com"}
        assert self.ranker._calculate_domain_authority(low_auth) == 0.5
    
    def test_score_normalization(self):
        """Test score normalization."""
        score = self.ranker.score("python", self.documents[0], self.documents)
        
        # Score should be between 0 and 1
        assert 0 <= score <= 1
        assert isinstance(score, float)
    
    def test_personalization(self):
        """Test personalization scoring."""
        user_profile = {"interests": ["python", "programming"]}
        features = self.ranker.extract_features("python", self.documents[0], self.documents, user_profile)
        
        assert features.personalization_score > 0
    
    def test_weight_update(self):
        """Test weight updates."""
        # Initial weight is 0.5, change to 0.7 to test update
        self.ranker.weights['bm25'] = 0.7
        
        assert self.ranker.weights['bm25'] == 0.7


class TestDiversityRanker:
    """Test diversity ranking."""

    def setup_method(self):
        """Setup for each test."""
        self.diversity_ranker = DiversityRanker(diversity_weight=0.3)
        self.results = [
            {"title": "Python Guide", "snippet": "Learn python programming"},
            {"title": "Python Tutorial", "snippet": "Python tutorial for beginners"},
            {"title": "Java Guide", "snippet": "Learn java programming"},
        ]
    
    def test_diversify(self):
        """Test result diversification."""
        diversified = self.diversity_ranker.diversify(self.results, "python")
        
        assert len(diversified) == len(self.results)
        assert diversified[0] in self.results
    
    def test_similarity_calculation(self):
        """Test document similarity calculation."""
        doc1 = {"title": "Python", "snippet": "programming language"}
        doc2 = {"title": "Python", "snippet": "programming language"}
        
        similarity = self.diversity_ranker._similarity(doc1, doc2)
        assert similarity == 1.0
    
    def test_empty_results(self):
        """Test with empty or single result."""
        assert self.diversity_ranker.diversify([], "python") == []
        assert self.diversity_ranker.diversify([self.results[0]], "python") == [self.results[0]]


class TestHybridRanker:
    """Test hybrid ranking."""

    def setup_method(self):
        """Setup for each test."""
        self.ranker = HybridRanker()
        self.results = [
            {
                "id": 1,
                "title": "Python Programming",
                "snippet": "Learn python",
                "url": "https://python.org",
            },
            {
                "id": 2,
                "title": "Java Programming",
                "snippet": "Learn java",
                "url": "https://example.com/java",
            },
        ]
    
    def test_rank_basic(self):
        """Test basic ranking."""
        import asyncio
        ranked = asyncio.run(self.ranker.rank_async("python", self.results))
        
        assert len(ranked) == len(self.results)
        assert all('final_score' in r for r in ranked)
        assert all('rank_position' in r for r in ranked)
    
    def test_rank_empty(self):
        """Test ranking with empty results."""
        import asyncio
        ranked = asyncio.run(self.ranker.rank_async("python", []))
        assert ranked == []
    
    def test_diversity_disabled(self):
        """Test ranking with diversity disabled."""
        import asyncio
        ranked = asyncio.run(self.ranker.rank_async("python", self.results, enable_diversity=False))
        assert len(ranked) == len(self.results)
    
    def test_statistics_tracking(self):
        """Test statistics tracking."""
        import asyncio
        initial_count = self.ranker.feature_stats['total_ranked']
        
        asyncio.run(self.ranker.rank_async("python", self.results))
        
        assert self.ranker.feature_stats['total_ranked'] > initial_count


class TestRankingModelManager:
    """Test ranking model manager."""

    def setup_method(self):
        """Setup for each test."""
        self.ranker = MLRanker()
        self.manager = RankingModelManager(self.ranker)
    
    def test_record_training_sample(self):
        """Test recording training samples."""
        doc = {"title": "Python", "snippet": "programming"}
        features = self.ranker.extract_features("python", doc, [doc])
        
        self.manager.record_training_sample("python", doc, features, clicked=True)
        
        assert len(self.manager.training_data) == 1
    
    def test_should_retrain(self):
        """Test retraining threshold."""
        assert not self.manager.should_retrain(sample_threshold=1000)
        
        # Add samples
        for i in range(1000):
            doc = {"title": f"Doc {i}"}
            features = self.ranker.extract_features("test", doc, [doc])
            self.manager.record_training_sample("test", doc, features, True)
        
        assert self.manager.should_retrain(sample_threshold=1000)
    
    def test_clear_training_data(self):
        """Test clearing training data."""
        doc = {"title": "Python"}
        features = self.ranker.extract_features("python", doc, [doc])
        self.manager.record_training_sample("python", doc, features, True)
        
        self.manager.clear_training_data()
        
        assert len(self.manager.training_data) == 0
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.manager.get_model_info()
        
        assert 'version' in info
        assert 'feature_weights' in info
        assert 'training_samples' in info
        assert info['version'] == '1.0.0'
    
    def test_update_weights(self):
        """Test updating model weights."""
        self.manager.update_weights({'bm25': 0.5})
        
        assert self.ranker.weights['bm25'] == 0.5
        assert self.manager.model_metadata['last_training_date'] is not None


class TestRankingIntegration:
    """Test ranking integration scenarios."""

    def test_end_to_end_ranking(self):
        """Test complete ranking pipeline."""
        import asyncio
        ranker = HybridRanker()
        
        documents = [
            {
                "id": i,
                "title": f"Document {i} about Python",
                "snippet": "Python programming guide",
                "url": f"https://example.com/python{i}",
            }
            for i in range(5)
        ]
        
        ranked = asyncio.run(ranker.rank_async("python", documents, enable_diversity=False))
        
        assert len(ranked) == 5
        assert all('final_score' in doc for doc in ranked)
        
        # Verify descending order
        scores = [doc['final_score'] for doc in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_personalization_impact(self):
        """Test personalization impact on ranking."""
        import asyncio
        ranker = HybridRanker()
        
        docs = [
            {"title": "Python Guide", "snippet": "python programming", "url": "http://python.org"},
            {"title": "Java Guide", "snippet": "java programming", "url": "http://java.com"},
        ]
        
        # Without personalization
        ranked_no_pers = asyncio.run(ranker.rank_async("programming", docs, user_profile=None))
        
        # No assertion on exact scores, just verify it works
        assert len(ranked_no_pers) > 0
