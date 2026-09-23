"""AI endpoint tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.schemas import SynthesizeResponse


@pytest.mark.asyncio
async def test_ai_ask_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/ai/ask", json={"prompt": "What is Python?"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_ask_success(client: AsyncClient, auth_headers: dict):
    with patch(
        "app.routes.ai.get_ai_answer",
        new=AsyncMock(return_value=("Python is a language.", "openai")),
    ):
        response = await client.post(
            "/api/v1/ai/ask",
            json={"prompt": "What is Python?"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["answer"]
    assert data["provider"] == "openai"


@pytest.mark.asyncio
async def test_ai_ask_not_found(client: AsyncClient, auth_headers: dict):
    with patch("app.routes.ai.get_ai_answer", new=AsyncMock(return_value=(None, "none"))):
        response = await client.post(
            "/api/v1/ai/ask",
            json={"prompt": "obscure query xyz"},
            headers=auth_headers,
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_synthesize(client: AsyncClient, auth_headers: dict):
    with patch(
        "app.routes.ai.synthesize_snippets",
        new=AsyncMock(return_value=SynthesizeResponse(synthesis="Summary text.", sources=["source1", "source2"])),
    ):
        response = await client.post(
            "/api/v1/ai/synthesize",
            json={"query": "python", "snippets": ["Snippet one", "Snippet two"]},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["synthesis"] == "Summary text."
