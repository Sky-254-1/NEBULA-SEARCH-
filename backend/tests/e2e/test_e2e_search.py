"""E2E tests — search flows."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_web_search_returns_results(e2e_client: AsyncClient, e2e_auth: dict):
    """Web search returns structured results from wikipedia backend."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    with patch("app.services.search.search_wikipedia", new_callable=AsyncMock) as mock_wiki:
        mock_wiki.return_value = [
            {"title": "Python", "snippet": "A programming language.", "url": "https://en.wikipedia.org/wiki/Python", "source": "wikipedia"},
        ]
        resp = await e2e_client.get(
            "/api/v1/search/web?q=python&backend=wikipedia",
            headers=headers,
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unified_search_hybrid_mode(e2e_client: AsyncClient, e2e_auth: dict):
    """Unified search in hybrid mode returns results."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    with patch("app.routes.search_unified.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value={
            "results": [{"id": 1, "title": "Test", "snippet": "snippet", "url": "https://t.co", "source": "web", "score": 0.8}],
            "ai_answer": None,
            "suggestions": [],
            "query": "test query",
            "response_time_ms": 15.0,
        })
        resp = await e2e_client.post(
            "/api/v1/search/",
            json={"query": "test query", "mode": "hybrid"},
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "hybrid"
    assert len(body["results"]) >= 1


@pytest.mark.asyncio
async def test_search_history_persisted(e2e_client: AsyncClient, e2e_auth: dict):
    """Performing a search records it in history."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    with patch("app.routes.search_unified.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value={
            "results": [],
            "ai_answer": None,
            "suggestions": [],
            "query": "history test",
            "response_time_ms": 5.0,
        })
        await e2e_client.post(
            "/api/v1/search/",
            json={"query": "history test", "mode": "web"},
            headers=headers,
        )

    resp = await e2e_client.get("/api/v1/search/history", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_save_and_list_saved_search(e2e_client: AsyncClient, e2e_auth: dict):
    """Save a search then retrieve it from saved searches."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    save_resp = await e2e_client.post(
        "/api/v1/search/save?query=saved+query&mode=hybrid",
        headers=headers,
    )
    assert save_resp.status_code == 200

    list_resp = await e2e_client.get("/api/v1/search/saved", headers=headers)
    assert list_resp.status_code == 200
    saved = list_resp.json()["data"]["saved"]
    assert any(s["query"] == "saved query" for s in saved)


@pytest.mark.asyncio
async def test_delete_saved_search(e2e_client: AsyncClient, e2e_auth: dict):
    """Save then delete a saved search."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    save_resp = await e2e_client.post(
        "/api/v1/search/save?query=to+delete&mode=hybrid",
        headers=headers,
    )
    saved_id = save_resp.json()["data"]["id"]

    del_resp = await e2e_client.delete(f"/api/v1/search/saved/{saved_id}", headers=headers)
    assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_search_v2_suggestions(e2e_client: AsyncClient, e2e_auth: dict):
    """V2 suggestions endpoint returns completions."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    resp = await e2e_client.get(
        "/api/v2/search/autocomplete?q=pyt",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "completions" in body


@pytest.mark.asyncio
async def test_search_spell_check(e2e_client: AsyncClient, e2e_auth: dict):
    """Spell-check endpoint returns correction status."""
    resp = await e2e_client.get("/api/v2/search/spell-check?q=pythong")
    assert resp.status_code == 200
    body = resp.json()
    assert "original" in body
    assert "corrected" in body
    assert "was_corrected" in body


@pytest.mark.asyncio
async def test_trending_endpoint(e2e_client: AsyncClient):
    """Trending endpoint returns trending queries."""
    resp = await e2e_client.get("/api/v2/search/trending?limit=5&hours=24")
    assert resp.status_code == 200
    body = resp.json()
    assert "trending" in body
    assert "period_hours" in body


@pytest.mark.asyncio
async def test_popular_endpoint(e2e_client: AsyncClient):
    """Popular endpoint returns popular queries."""
    resp = await e2e_client.get("/api/v2/search/popular?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert "popular" in body
