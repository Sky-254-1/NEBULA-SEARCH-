"""Orchestrator tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.search.orchestrator import expand_query, orchestrate_search, _dedupe_results, _rank_results


def test_expand_query():
    variants = expand_query("python programming language")
    assert variants[0] == "python programming language"
    assert len(variants) >= 1


def test_dedupe_results():
    items = [
        {"title": "A", "url": "https://example.com/a", "snippet": "", "source": "w"},
        {"title": "B", "url": "https://example.com/a", "snippet": "", "source": "w"},
    ]
    assert len(_dedupe_results(items)) == 1


def test_rank_results():
    ranked = _rank_results(
        [
            {"title": "Other", "snippet": "misc", "url": "1", "source": "w"},
            {"title": "Python guide", "snippet": "python tutorial", "url": "2", "source": "w"},
        ],
        "python",
    )
    assert ranked[0]["title"] == "Python guide"


@pytest.mark.asyncio
async def test_orchestrate_search_mocked():
    mock_results = [
        {"title": "Test", "snippet": "Snippet", "url": "https://example.com", "source": "wikipedia"}
    ]
    with patch("app.search.orchestrator.run_web_search", new=AsyncMock(return_value=mock_results)):
        payload = await orchestrate_search("test query", ["wikipedia"], use_cache=False)
    assert payload["total"] >= 1
    assert payload["results"][0]["title"] == "Test"
