"""Extended tests for Search Service providers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.search import search_wikipedia, search_brave, search_serpapi, run_web_search
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_search_wikipedia_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "query": {
            "search": [
                {"title": "Test Page", "snippet": "Test <p>Snippet</p>", "pageid": 123}
            ]
        }
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        results = await search_wikipedia("test query", 1, 10)
        assert len(results) == 1
        assert results[0]["title"] == "Test Page"
        assert "Test Snippet" in results[0]["snippet"]
        assert "wikipedia" in results[0]["url"]

@pytest.mark.asyncio
async def test_search_brave_success():
    with patch("app.services.search.settings") as mocked_settings:
        mocked_settings.brave_api_key = "test-key"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "web": {
                "results": [
                    {"title": "Brave Title", "description": "Brave Desc", "url": "https://brave.com"}
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            results = await search_brave("test", 1, 10)
            assert results[0]["title"] == "Brave Title"

@pytest.mark.asyncio
async def test_search_brave_no_key():
    with patch("app.services.search.settings") as mocked_settings:
        mocked_settings.brave_api_key = None
        with pytest.raises(HTTPException) as exc:
            await search_brave("test", 1, 10)
        assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_search_serpapi_success():
    with patch("app.services.search.settings") as mocked_settings:
        mocked_settings.serpapi_key = "test-key"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "organic_results": [
                {"title": "Serp Title", "snippet": "Serp Snippet", "link": "https://google.com"}
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            results = await search_serpapi("test", 1, 10)
            assert results[0]["title"] == "Serp Title"

@pytest.mark.asyncio
async def test_run_web_search_dispatch():
    with patch("app.services.search.search_wikipedia", new_callable=AsyncMock) as mock_wiki:
        mock_wiki.return_value = [{"title": "Wiki"}]
        res = await run_web_search("query", "wikipedia", 1, 10)
        assert res[0]["title"] == "Wiki"

    with patch("app.services.search.search_brave", new_callable=AsyncMock) as mock_brave:
        mock_brave.return_value = [{"title": "Brave"}]
        res = await run_web_search("query", "brave", 1, 10)
        assert res[0]["title"] == "Brave"

    with patch("app.services.search.search_serpapi", new_callable=AsyncMock) as mock_serp:
        mock_serp.return_value = [{"title": "Serp"}]
        res = await run_web_search("query", "serpapi", 1, 10)
        assert res[0]["title"] == "Serp"
