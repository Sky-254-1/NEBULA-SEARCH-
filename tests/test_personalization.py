"""Tests for personalization engine."""

import pytest
from datetime import datetime

from app.search.personalization import PersonalizationEngine, UserProfile


class TestUserProfile:
    """Test UserProfile class."""

    def test_profile_creation(self):
        """Test creating a user profile."""
        profile = UserProfile(1)
        assert profile.user_id == 1
        assert profile.interests == []
        assert profile.frequent_queries == []
        assert profile.personalization_enabled is True

    def test_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "user_id": 1,
            "interests": ["python", "programming"],
            "frequent_queries": '["python tutorial", "learn python"]',
            "preferred_categories": '["technology", "tutorials"]',
            "personalization_enabled": True,
        }
        profile = UserProfile.from_dict(1, data)
        
        assert profile.user_id == 1
        assert profile.interests == ["python", "programming"]
        assert profile.frequent_queries == ["python tutorial", "learn python"]
        assert profile.preferred_categories == ["technology", "tutorials"]

    def test_to_dict(self):
        """Test converting profile to dictionary."""
        profile = UserProfile(1)
        profile.interests = ["python"]
        profile.frequent_queries = ["python tutorial"]
        profile.preferred_categories = ["technology"]
        
        data = profile.to_dict()
        
        assert data["user_id"] == 1
        assert data["interests"] == ["python"]
        assert data["frequent_queries"] == ["python tutorial"]
        assert data["preferred_categories"] == ["technology"]


class TestPersonalizationEngine:
    """Test PersonalizationEngine class."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = PersonalizationEngine(db=None)

    def test_extract_interests(self):
        """Test interest extraction from search history."""
        history = [
            {"query": "python programming tutorial", "frequency": 5},
            {"query": "python django web framework", "frequency": 3},
            {"query": "javascript tutorial for beginners", "frequency": 2},
            {"query": "python data science", "frequency": 4},
        ]
        
        interests = self.engine._extract_interests(history, top_k=10)
        
        # Should extract python, programming, tutorial, django, etc.
        assert "python" in interests
        assert "programming" in interests or "tutorial" in interests
        assert len(interests) <= 10

    def test_extract_interests_filters_stopwords(self):
        """Test that stop words are filtered out."""
        history = [
            {"query": "the quick brown fox", "frequency": 1},
            {"query": "a quick brown fox", "frequency": 1},
        ]
        
        interests = self.engine._extract_interests(history, top_k=10)
        
        # Should not contain stop words
        assert "the" not in interests
        assert "a" not in interests
        assert "quick" in interests
        assert "brown" in interests

    def test_calculate_interest_weights(self):
        """Test calculating interest weights."""
        history = [
            {"query": "python programming", "frequency": 5, "last_used": datetime.now().isoformat()},
            {"query": "python django", "frequency": 3, "last_used": datetime.now().isoformat()},
        ]
        
        weights = self.engine._calculate_interest_weights(history)
        
        assert "python" in weights
        assert weights["python"] > 0
        # All weights should be normalized to 0-1
        assert all(0 <= w <= 1 for w in weights.values())

    def test_calculate_interest_weights_with_recency(self):
        """Test that recency affects weights."""
        now = datetime.now().isoformat()
        old = (datetime.now() - __import__('datetime').timedelta(days=365)).isoformat()
        
        history = [
            {"query": "python programming", "frequency": 5, "last_used": now},
            {"query": "old topic", "frequency": 5, "last_used": old},
        ]
        
        weights = self.engine._calculate_interest_weights(history)
        
        # Recent queries should have higher weights
        assert weights.get("python", 0) > weights.get("topic", 0)

    def test_calculate_category_weights(self):
        """Test category weight calculation."""
        categories = ["technology", "tutorials", "programming"]
        weights = self.engine._calculate_category_weights(categories)
        
        assert len(weights) == 3
        assert all(w == 1/3 for w in weights.values())

    def test_calculate_category_weights_empty(self):
        """Test category weights with empty list."""
        weights = self.engine._calculate_category_weights([])
        assert weights == {}

    def test_calculate_result_score_adjustment_enabled(self):
        """Test score adjustment with enabled profile."""
        profile = UserProfile(1)
        profile.personalization_enabled = True
        profile.interests = ["python", "programming"]
        profile.preferred_categories = ["technology"]
        
        doc = {
            "title": "Python Programming Guide",
            "snippet": "Learn Python programming"
        }
        
        adjustment = self.engine.calculate_result_score_adjustment(profile, doc)
        
        # Should have positive adjustment for interest matches
        assert adjustment > 0
        assert adjustment <= 0.2  # Cap at 0.2

    def test_calculate_result_score_adjustment_disabled(self):
        """Test score adjustment with disabled profile."""
        profile = UserProfile(1)
        profile.personalization_enabled = False
        profile.interests = ["python"]
        
        doc = {"title": "Python Programming", "snippet": "Learn Python"}
        
        adjustment = self.engine.calculate_result_score_adjustment(profile, doc)
        
        assert adjustment == 0.0

    def test_calculate_result_score_adjustment_no_match(self):
        """Test score adjustment with no matches."""
        profile = UserProfile(1)
        profile.personalization_enabled = True
        profile.interests = ["javascript"]
        
        doc = {"title": "Python Programming", "snippet": "Learn Python"}
        
        adjustment = self.engine.calculate_result_score_adjustment(profile, doc)
        
        assert adjustment == 0.0

    def test_get_user_profile_no_db(self):
        """Test getting user profile without database."""
        import asyncio
        profile = asyncio.run(self.engine.get_user_profile(1))
        
        assert profile.user_id == 1
        assert profile.interests == []
        assert profile.personalization_enabled is True

    def test_learn_from_search_no_db(self):
        """Test learning from search without database."""
        import asyncio
        
        async def test_async():
            # Should not raise error
            await self.engine.learn_from_search(1, "python programming")
        
        asyncio.run(test_async())

    def test_get_personalized_weights_disabled(self):
        """Test getting personalized weights when disabled."""
        import asyncio
        
        async def test():
            profile = await self.engine.get_user_profile(1)
            profile.personalization_enabled = False
            
            weights = await self.engine.get_personalized_weights(1, {"bm25": 0.5, "personalization": 0.1})
            
            assert weights == {"bm25": 0.5, "personalization": 0.1}
        
        asyncio.run(test())

    def test_score_adjustment_capped(self):
        """Test that score adjustment is capped at 0.2."""
        profile = UserProfile(1)
        profile.personalization_enabled = True
        profile.interests = ["python", "programming", "tutorial", "guide", "learn"]
        profile.preferred_categories = ["tech", "education", "tutorials"]
        
        doc = {
            "title": "Python Programming Tutorial Guide - Learn Programming",
            "snippet": "Learn Python programming with this comprehensive tutorial guide"
        }
        
        adjustment = self.engine.calculate_result_score_adjustment(profile, doc)
        
        # Should be capped at 0.2
        assert adjustment <= 0.2


class TestPersonalizationIntegration:
    """Test personalization integration with ranking."""

    def test_personalization_with_ranker(self):
        """Test personalization integration with hybrid ranker."""
        import asyncio
        from app.search.ranking import HybridRanker
        from app.search.personalization import PersonalizationEngine, UserProfile
        
        engine = PersonalizationEngine(db=None)
        ranker = HybridRanker(personalization_engine=engine)
        
        # Create a user profile with interests
        profile = UserProfile(1)
        profile.interests = ["python", "programming"]
        
        results = [
            {
                "id": 1,
                "title": "Python Programming Guide",
                "snippet": "Learn Python programming",
                "url": "https://python.org",
            },
            {
                "id": 2,
                "title": "Java Tutorial",
                "snippet": "Learn Java programming",
                "url": "https://java.com",
            },
        ]
        
        ranked = asyncio.run(ranker.rank("python", results, user_profile=profile, enable_diversity=False))
        
        assert len(ranked) == 2
        assert all('final_score' in r for r in ranked)
        assert all('rank_position' in r for r in ranked)
        
        # Python result should be ranked higher
        assert ranked[0]['id'] == 1
        assert ranked[0]['personalization_adjustment'] > 0
