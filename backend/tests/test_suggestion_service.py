"""Behavioral tests for SuggestionService.

SuggestionService imports cache_service at module load time (line 12 of
suggestion_service.py).  The conftest.py does NOT mock this, so the import
succeeds.  We mock cache_service.get/set at the module path for each test.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.suggestion_service import SuggestionService


class TestSuggestionService:
    """Tests for SuggestionService with mocked DB and cache."""

    @pytest.fixture(autouse=True)
    def _patch_cache(self, monkeypatch):
        """Mock cache_service at the suggestion_service module path."""
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)  # cache miss by default
        mock_cache.set = AsyncMock(return_value=True)
        monkeypatch.setattr(
            "app.services.suggestion_service.cache_service", mock_cache
        )
        return mock_cache

    @pytest.fixture
    def svc(self):
        db = MagicMock()
        db.fetchall = AsyncMock(return_value=[])
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return SuggestionService(db)

    @pytest.mark.asyncio
    async def test_get_suggestions_cache_miss(self, svc):
        """Happy path: cache miss, gather from sources, return ranked."""
        result = await svc.get_suggestions("py", limit=3)
        assert result["cache_hit"] is False
        assert "query" in result
        assert "suggestions" in result
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_get_suggestions_cache_hit(self, svc, _patch_cache):
        """Cache hit returns cached response immediately."""
        _patch_cache.get.return_value = {
            "query": "py", "suggestions": [],
            "cache_hit": True, "latency_ms": 1,
        }
        result = await svc.get_suggestions("py")
        assert result["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_get_suggestions_with_user_id(self, svc):
        """When user_id is provided, personalized suggestions are included."""
        svc._repo.get_user_search_history = AsyncMock(return_value=[
            {"query": "python"}, {"query": "pytest"}
        ])
        result = await svc.get_suggestions("py", user_id=1)
        assert result["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_get_suggestions_with_session_id(self, svc):
        """When session_id is provided, search is recorded."""
        svc._repo.record_search = AsyncMock()
        result = await svc.get_suggestions("py", session_id="sess1")
        svc._repo.record_search.assert_awaited_once()
        assert result["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_get_trending_suggestions_cache_miss(self, svc):
        """Trending suggestions fetched from DB on cache miss."""
        result = await svc.get_trending_suggestions("py")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_trending_suggestions_cache_hit(self, svc, _patch_cache):
        """Trending suggestions returned from cache."""
        _patch_cache.get.return_value = [{"text": "python", "type": "trending"}]
        result = await svc.get_trending_suggestions("py")
        assert len(result) == 1
        assert result[0]["text"] == "python"

    @pytest.mark.asyncio
    async def test_get_related_suggestions_cache_miss(self, svc):
        """Related suggestions fetched from repo on cache miss."""
        svc._repo.get_related_searches = AsyncMock(return_value=[])
        result = await svc.get_related_suggestions("py")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_related_suggestions_cache_hit(self, svc, _patch_cache):
        """Related suggestions returned from cache."""
        _patch_cache.get.return_value = [{"text": "python", "type": "related"}]
        result = await svc.get_related_suggestions("py")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_record_search_empty_query(self, svc):
        """Empty query is silently ignored."""
        svc._repo.record_search = AsyncMock()
        await svc.record_search("   ", user_id=1, session_id="s1")
        svc._repo.record_search.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_search_valid(self, svc):
        """Valid query is recorded and trending is incremented."""
        svc._repo.record_search = AsyncMock()
        svc._repo.increment_trending_query = AsyncMock()
        await svc.record_search("python", user_id=1, session_id="s1")
        svc._repo.record_search.assert_awaited_once()
        svc._repo.increment_trending_query.assert_awaited_once_with("python")

    @pytest.mark.asyncio
    async def test_record_search_with_click(self, svc):
        """Click-through triggers related search score update."""
        svc._repo.record_search = AsyncMock()
        svc._repo.increment_trending_query = AsyncMock()
        svc._repo.get_session_searches = AsyncMock(return_value=["python", "py"])
        svc._repo.increment_related_search_clicks = AsyncMock()
        await svc.record_search(
            "python", user_id=1, session_id="s1", clicked_result_id=42
        )
        svc._repo.increment_related_search_clicks.assert_awaited()

    @pytest.mark.asyncio
    async def test_refresh_trending(self, svc):
        """Refresh trending returns row count and duration."""
        svc._repo.update_trending_metrics = AsyncMock(return_value=5)
        result = await svc.refresh_trending()
        assert result["rows_updated"] == 5
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_refresh_related_searches(self, svc):
        """Refresh related searches returns relationship count."""
        svc._repo.rebuild_related_searches = AsyncMock(return_value=10)
        result = await svc.refresh_related_searches()
        assert result["relationships"] == 10
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_refresh_semantic_suggestions(self, svc):
        """Refresh semantic suggestions returns count."""
        result = await svc.refresh_semantic_suggestions()
        assert "suggestions" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_rank_and_deduplicate_empty(self, svc):
        """Empty suggestions list returns empty list."""
        result = await svc._rank_and_deduplicate([], limit=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_rank_and_deduplicate_duplicates(self, svc):
        """Duplicate suggestions are deduplicated, keeping higher score."""
        suggestions = [
            {"text": "python", "type": "trending", "score": 0.5},
            {"text": "Python", "type": "semantic", "score": 0.9},
        ]
        result = await svc._rank_and_deduplicate(suggestions, limit=5)
        assert len(result) == 1
        assert result[0]["score"] == 1.0  # normalized

    @pytest.mark.asyncio
    async def test_get_personalized_suggestions(self, svc):
        """Personalized suggestions from user history."""
        svc._repo.get_user_search_history = AsyncMock(return_value=[
            {"query": "python"}, {"query": "pytest"}, {"query": "pyramid"}
        ])
        result = await svc._get_personalized_suggestions("py", user_id=1)
        assert len(result) > 0
        for s in result:
            assert s["type"] == "personalized"

    @pytest.mark.asyncio
    async def test_get_personalized_suggestions_no_match(self, svc):
        """No personalized suggestions when history doesn't match prefix."""
        svc._repo.get_user_search_history = AsyncMock(return_value=[
            {"query": "java"}, {"query": "ruby"}
        ])
        result = await svc._get_personalized_suggestions("py", user_id=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_handle_click_through(self, svc):
        """Click-through updates related search scores."""
        svc._repo.get_session_searches = AsyncMock(
            return_value=["python", "py", "pytest"]
        )
        svc._repo.increment_related_search_clicks = AsyncMock()
        await svc._handle_click_through("python", "sess1", 42)
        assert svc._repo.increment_related_search_clicks.await_count >= 1