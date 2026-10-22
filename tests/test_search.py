"""Search endpoint tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_web_search_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/search/web", params={"q": "python"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_web_search_wikipedia(client: AsyncClient, auth_headers: dict):
    mock_results = [
        {
            "document_id": 1,
            "chunk_id": 1,
            "filename": "wikipedia-python",
            "content": "Python is a programming language",
            "score": 0.95,
            "vector_score": 0.9,
            "keyword_score": 1.0,
        }
    ]
    with patch("app.routes.search.run_web_search", new=AsyncMock(return_value=mock_results)):
        response = await client.get(
            "/api/v1/search/web",
            params={"q": "python", "backend": "wikipedia"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "wikipedia-python"


@pytest.mark.asyncio
async def test_web_search_unknown_backend(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/v1/search/web",
        params={"q": "test", "backend": "invalid"},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_sanitize_query():
    from app.services.search import sanitize_query

    assert sanitize_query("  hello\x00world  ") == "helloworld"
