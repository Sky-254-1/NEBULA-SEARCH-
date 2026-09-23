"""AI service unit tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import SynthesizeResponse
from app.services.ai import get_ai_answer, synthesize_snippets


@pytest.mark.asyncio
async def test_synthesize_fallback_without_openai():
    with patch("app.services.ai.router") as mock_router:
        mock_router.complete = AsyncMock(return_value=(None, "none"))
        result = await synthesize_snippets(
            "python programming",
            ["Python is a language.", "It is popular."],
        )
    assert isinstance(result, SynthesizeResponse)
    assert len(result.synthesis) > 0


@pytest.mark.asyncio
async def test_get_ai_answer_from_router():
    with patch("app.services.ai.router") as mock_router:
        mock_router.complete = AsyncMock(return_value=("Fallback answer", "duckduckgo"))
        answer, provider = await get_ai_answer("what is python", use_cache=False)
    assert answer == "Fallback answer"
    assert provider == "duckduckgo"
