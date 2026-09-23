"""Tests for the unified search API endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unified_search_requires_auth(async_client: AsyncClient):
    """Unified search endpoint requires authentication."""
    resp = await async_client.post(
        "/api/v1/search/",
        json={"query": "python", "mode": "hybrid"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_unified_search_returns_results(async_client: AsyncClient, auth_headers: dict):
    """Unified search returns a structured response."""
    with patch("app.routes.search_unified.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value={
            "results": [
                {
                    "id": 1,
                    "title": "Python (programming language)",
                    "snippet": "Python is a high-level language.",
                    "url": "https://en.wikipedia.org/wiki/Python",
                    "source": "wikipedia",
                    "score": 0.9,
                }
            ],
            "ai_answer": None,
            "suggestions": ["python tutorial", "python docs"],
            "query": "python",
            "response_time_ms": 42.0,
        })
        resp = await async_client.post(
            "/api/v1/search/",
            json={"query": "python", "mode": "web"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert body["query"] == "python"
    assert body["mode"] == "web"
    assert isinstance(body["results"], list)


@pytest.mark.asyncio
async def test_unified_search_ai_mode(async_client: AsyncClient, auth_headers: dict):
    """AI mode includes an ai_answer in the response."""
    with patch("app.routes.search_unified.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value={
            "results": [],
            "ai_answer": {"answer": "Python is a language.", "provider": "openai", "citations": []},
            "suggestions": [],
            "query": "what is python",
            "response_time_ms": 100.0,
        })
        resp = await async_client.post(
            "/api/v1/search/",
            json={"query": "what is python", "mode": "ai", "include_ai_answer": True},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ai_answer"] is not None
    assert body["ai_answer"]["answer"] == "Python is a language."


@pytest.mark.asyncio
async def test_unified_search_invalid_mode(async_client: AsyncClient, auth_headers: dict):
    """Invalid mode returns validation error."""
    resp = await async_client.post(
        "/api/v1/search/",
        json={"query": "python", "mode": "invalid_mode"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_unified_search_empty_query(async_client: AsyncClient, auth_headers: dict):
    """Empty query returns validation error."""
    resp = await async_client.post(
        "/api/v1/search/",
        json={"query": "", "mode": "web"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_suggestions(async_client: AsyncClient, auth_headers: dict):
    """Suggestions endpoint returns list of suggestions."""
    with patch("app.routes.search_unified.query_suggestion_engine") as mock_engine:
        suggestion = MagicMock()
        suggestion.suggestion = "python tutorial"
        suggestion.score = 0.9
        suggestion.source = "history"
        mock_engine.get_suggestions = AsyncMock(return_value=[suggestion])
        resp = await async_client.get(
            "/api/v1/search/suggestions?q=pyth",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "suggestions" in body["data"]


@pytest.mark.asyncio
async def test_search_history(async_client: AsyncClient, auth_headers: dict):
    """Search history endpoint returns user history."""
    resp = await async_client.get(
        "/api/v1/search/history",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "history" in body["data"]


@pytest.mark.asyncio
async def test_clear_search_history(async_client: AsyncClient, auth_headers: dict):
    """Clear history endpoint returns success."""
    resp = await async_client.delete(
        "/api/v1/search/history",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_save_search(async_client: AsyncClient, auth_headers: dict):
    """Save search endpoint stores the query."""
    resp = await async_client.post(
        "/api/v1/search/save?query=machine+learning&mode=hybrid",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["query"] == "machine learning"


@pytest.mark.asyncio
async def test_list_saved_searches(async_client: AsyncClient, auth_headers: dict):
    """List saved searches endpoint returns saved searches."""
    resp = await async_client.get(
        "/api/v1/search/saved",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "saved" in body["data"]


@pytest.mark.asyncio
async def test_delete_saved_search_not_found(async_client: AsyncClient, auth_headers: dict):
    """Delete non-existent saved search returns 404."""
    resp = await async_client.delete(
        "/api/v1/search/saved/99999",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unified_search_with_facets(async_client: AsyncClient, auth_headers: dict):
    """Facets are computed and returned when requested."""
    with patch("app.routes.search_unified.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value={
            "results": [
                {"id": 1, "title": "Wikipedia article", "snippet": "Info", "url": "https://en.wikipedia.org/wiki/Test", "source": "wikipedia", "score": 0.8},
                {"id": 2, "title": "Brave result", "snippet": "Info 2", "url": "https://example.com/page", "source": "brave", "score": 0.7},
            ],
            "ai_answer": None,
            "suggestions": [],
            "query": "test",
            "response_time_ms": 30.0,
        })
        resp = await async_client.post(
            "/api/v1/search/",
            json={"query": "test", "mode": "web", "facets": ["source"]},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["facets"] is not None
    sources = {f["value"] for f in body["facets"]}
    assert "wikipedia" in sources or "brave" in sources
