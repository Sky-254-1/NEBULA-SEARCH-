"""Extended tests for AI providers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.providers.ai.openai import OpenAIProvider
from app.providers.ai.ollama import OllamaProvider
from app.providers.ai.router import AIProviderRouter

@pytest.mark.asyncio
async def test_openai_provider_success():
    with patch("app.providers.ai.openai.settings") as mocked_settings:
        mocked_settings.openai_api_key = "test-key"
        mocked_settings.openai_base_url = "https://api.openai.com/v1"
        mocked_settings.openai_model = "gpt-4"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "OpenAI Response"}}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            provider = OpenAIProvider()
            resp = await provider.complete("hi")
            assert resp == "OpenAI Response"

@pytest.mark.asyncio
async def test_openai_provider_stream():
    with patch("app.providers.ai.openai.settings") as mocked_settings:
        mocked_settings.openai_api_key = "test-key"
        mocked_settings.openai_base_url = "https://api.openai.com/v1"

        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: {"choices": [{"delta": {"content": " World"}}]}'
            yield 'data: [DONE]'

        mock_resp = AsyncMock()
        mock_resp.aiter_lines = mock_aiter_lines
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_resp

        with patch("httpx.AsyncClient.stream", return_value=mock_client.stream()):
            provider = OpenAIProvider()
            chunks = []
            async for chunk in provider.stream("hi"):
                chunks.append(chunk)
            assert "".join(chunks) == "Hello World"

@pytest.mark.asyncio
async def test_ollama_provider_success():
    with patch("app.providers.ai.ollama.settings") as mocked_settings:
        mocked_settings.ollama_base_url = "http://localhost:11434"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"content": "Ollama Response"}}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            provider = OllamaProvider()
            # Assuming complete() exists based on router.py usage
            resp = await provider.complete("hi")
            assert resp == "Ollama Response"

@pytest.mark.asyncio
async def test_ai_router_dispatch():
    mock_openai = MagicMock(spec=OpenAIProvider)
    mock_openai.complete = AsyncMock(return_value="OpenAI")

    with patch("app.providers.ai.router.OpenAIProvider", return_value=mock_openai), \
         patch("app.providers.ai.router.settings") as mocked_settings:

        mocked_settings.ai_provider = "openai"
        router = AIProviderRouter()
        resp, name = await router.complete("hi")
        assert resp == "OpenAI"
        assert name == "openai"
