"""Search service unit tests."""

import pytest
from fastapi import HTTPException

from app.services.search import ALLOWED_BACKENDS, run_web_search, sanitize_query


def test_allowed_backends():
    assert "wikipedia" in ALLOWED_BACKENDS
    assert "brave" in ALLOWED_BACKENDS
    assert "serpapi" in ALLOWED_BACKENDS


def test_sanitize_strips_control_chars():
    assert sanitize_query("hello\x00world") == "helloworld"
    assert sanitize_query("  spaced  ") == "spaced"


@pytest.mark.asyncio
async def test_run_web_search_unknown_backend():
    with pytest.raises(HTTPException) as exc:
        await run_web_search("test", "bing", 1, 10)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_run_web_search_empty_after_sanitize():
    with pytest.raises(HTTPException) as exc:
        await run_web_search("\x00\x01", "wikipedia", 1, 10)
    assert exc.value.status_code == 400
