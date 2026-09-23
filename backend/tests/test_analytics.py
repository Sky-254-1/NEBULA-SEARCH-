"""Tests for analytics endpoints."""

import pytest
from unittest.mock import AsyncMock

from app.database.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
from app.services.analytics_metrics import record_search_query, record_click_event


@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetchone = AsyncMock()
    db.fetchall = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_cursor():
    """Mock database cursor."""
    cursor = AsyncMock()
    cursor.fetchone = AsyncMock()
    cursor.fetchall = AsyncMock()
    return cursor


@pytest.fixture
def analytics_repo(mock_db):
    """Create analytics repository with mock DB."""
    return AnalyticsRepository(mock_db)


@pytest.fixture
def analytics_service(mock_db):
    """Create analytics service with mock DB."""
    return AnalyticsService(mock_db, redis_client=None)


class TestAnalyticsRepository:
    """Test analytics repository."""

    @pytest.mark.asyncio
    async def test_record_search_event(self, analytics_repo, mock_db, mock_cursor):
        """Test recording a search event."""
        mock_cursor.fetchone.return_value = (42,)
        mock_db.execute.return_value = mock_cursor
        
        event_id = await analytics_repo.record_search_event(
            query="test query",
            user_id=1,
            session_id="session-123",
            search_backend="unified",
            search_type="hybrid",
            results_count=10,
            response_time_ms=45.5,
            clicked_result=None,
            device="desktop",
        )
        
        assert event_id == 42
        assert mock_db.execute.call_count >= 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_click_event(self, analytics_repo, mock_db):
        """Test recording a click event."""
        await analytics_repo.record_click_event(
            search_event_id=1,
            query="test",
            document_id=5,
            rank_position=2,
            time_to_click=3.5,
            user_id=1,
        )
        
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_response_time(self, analytics_repo, mock_db):
        """Test recording response time metrics."""
        await analytics_repo.record_response_time(
            total_latency=100.0,
            db_latency=20.0,
            redis_latency=10.0,
            semantic_latency=30.0,
            bm25_latency=20.0,
            ranking_latency=10.0,
            snippet_latency=5.0,
            api_latency=5.0,
        )
        
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_popular_queries(self, analytics_repo, mock_db):
        """Test getting popular queries."""
        mock_rows = [
            {"query": "python", "count": 100},
            {"query": "fastapi", "count": 80},
        ]
        mock_db.fetchall.return_value = mock_rows
        
        result = await analytics_repo.get_popular_queries(limit=10, days=30)
        
        assert len(result) == 2
        assert result[0]["query"] == "python"
        assert result[0]["count"] == 100

    @pytest.mark.asyncio
    async def test_get_zero_result_queries(self, analytics_repo, mock_db):
        """Test getting zero-result queries."""
        mock_rows = [
            {"query": "xyz", "count": 50},
        ]
        mock_db.fetchall.return_value = mock_rows
        
        result = await analytics_repo.get_zero_result_queries(limit=10, days=30)
        
        assert len(result) == 1
        assert result[0]["query"] == "xyz"

    @pytest.mark.asyncio
    async def test_get_response_time_stats(self, analytics_repo, mock_db):
        """Test getting response time statistics."""
        mock_db.fetchall.return_value = [
            {"avg": 45.0, "median": 40.0, "max": 200.0, "total": 1000}
        ]
        
        result = await analytics_repo.get_response_time_stats(days=7)
        
        assert "average" in result
        assert "median" in result
        assert "p95" in result
        assert "p99" in result
        assert result["average"] == 45.0

    @pytest.mark.asyncio
    async def test_get_query_trends(self, analytics_repo, mock_db):
        """Test getting query trends."""
        mock_rows = [
            {"date": "2026-07-01", "queries": 100, "unique_users": 50, "zero_results": 5},
        ]
        mock_db.fetchall.return_value = mock_rows
        
        result = await analytics_repo.get_query_trends(period="daily", days=30)
        
        assert len(result) == 1
        assert result[0]["date"] == "2026-07-01"

    @pytest.mark.asyncio
    async def test_get_dashboard_overview(self, analytics_repo, mock_db):
        """Test getting dashboard overview."""
        mock_db.fetchone.side_effect = [
            {"count": 1000},  # total_queries
            {"count": 100},   # unique_users
            {"avg": 45.0},    # avg_response
            {"count": 20},    # zero_results
            {"count": 150},   # total_clicks
        ]
        
        result = await analytics_repo.get_dashboard_overview(period="24h")
        
        assert "total_queries" in result
        assert "unique_users" in result
        assert "average_response_time_ms" in result
        assert "zero_result_rate" in result
        assert "click_through_rate" in result
        assert result["total_queries"] == 1000

    @pytest.mark.asyncio
    async def test_get_user_analytics(self, analytics_repo, mock_db):
        """Test getting user analytics."""
        mock_db.fetchone.side_effect = [
            {"count": 50},   # search_count
            {"avg": 40.0},   # avg_session
            {"search_type": "hybrid"},  # search_type
        ]
        mock_db.fetchall.return_value = [
            {"document_id": 1, "clicks": 10},
        ]
        
        result = await analytics_repo.get_user_analytics(user_id=1, days=30)
        
        assert "searches" in result
        assert "preferred_search_type" in result

    @pytest.mark.asyncio
    async def test_get_click_analytics(self, analytics_repo, mock_db):
        """Test getting click analytics."""
        mock_db.fetchone.side_effect = [
            {"count": 150},   # total_clicks
            {"avg": 3.5},     # avg_position
        ]
        mock_db.fetchall.return_value = [
            {"document_id": 1, "clicks": 20},
        ]
        
        result = await analytics_repo.get_click_analytics(days=7)
        
        assert "total_clicks" in result
        assert "avg_click_position" in result

    @pytest.mark.asyncio
    async def test_get_search_quality_metrics(self, analytics_repo, mock_db):
        """Test getting search quality metrics."""
        mock_db.fetchone.side_effect = [
            {"total_queries": 1000, "zero_results": 20, "avg_response_time": 45.0},
            {"count": 300},  # semantic_usage
            {"count": 700},  # hybrid_usage
        ]
        
        result = await analytics_repo.get_search_quality_metrics(days=30)
        
        assert "zero_result_rate" in result
        assert "avg_response_time" in result


class TestAnalyticsService:
    """Test analytics service."""

    @pytest.mark.asyncio
    async def test_record_search(self, analytics_service, mock_db, mock_cursor):
        """Test recording a search via service."""
        mock_cursor.fetchone.return_value = (42,)
        mock_db.execute.return_value = mock_cursor
        
        event_id = await analytics_service.record_search(
            query="test",
            user_id=1,
            session_id="session-123",
            search_backend="unified",
            search_type="hybrid",
            results_count=10,
            response_time_ms=45.0,
            clicked_result=None,
            device="desktop",
        )
        
        assert event_id == 42

    @pytest.mark.asyncio
    async def test_get_dashboard(self, analytics_service, mock_db, mock_cursor):
        """Test getting dashboard."""
        mock_db.fetchone.side_effect = [
            {"count": 1000},
            {"count": 100},
            {"avg": 45.0},
            {"count": 20},
            {"count": 150},
        ]
        mock_db.fetchall.side_effect = [
            [{"avg": 45.0, "median": 45.0, "max": 100.0, "total": 1000}],
            [{"query": "python", "count": 100}],
            [],
            [],
        ]
        
        result = await analytics_service.get_dashboard(period="24h")
        
        assert "total_queries" in result
        assert "popular_searches" in result
        assert "response_times" in result

    @pytest.mark.asyncio
    async def test_get_popular(self, analytics_service, mock_db):
        """Test getting popular searches."""
        mock_db.fetchall.return_value = [
            {"query": "python", "count": 100},
        ]
        
        result = await analytics_service.get_popular(limit=10, days=30)
        
        assert len(result) == 1
        assert result[0]["query"] == "python"


class TestAnalyticsMetrics:
    """Test analytics metrics."""

    def test_record_search_query(self):
        """Test recording search query metric."""
        # Should not raise
        record_search_query("hybrid", "unified")

    def test_record_click_event(self):
        """Test recording click event metric."""
        # Should not raise
        record_click_event("test query")