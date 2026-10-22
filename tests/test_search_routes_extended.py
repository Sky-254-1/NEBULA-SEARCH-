"""Extended tests for Search routes."""

import pytest
import pytest_asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture
async def search_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_web_search_error_handling(search_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()

    # Mock rate limit
    from app.middleware.rate_limit import rate_limit
    app.dependency_overrides[rate_limit] = lambda: None

    with patch("app.routes.search.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.search.run_web_search", new_callable=AsyncMock) as mock_run:

        mock_get_id.return_value = 1

        # Test HTTPStatusError
        mock_run.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock(status_code=500))
        response = await search_client.get("/api/v1/search/web?q=test&backend=wikipedia")
        assert response.status_code == 502
        assert "Search backend error: 500" in response.json()["detail"]

        # Test RequestError
        mock_run.side_effect = httpx.RequestError("Unreachable")
        response = await search_client.get("/api/v1/search/web?q=test&backend=wikipedia")
        assert response.status_code == 502
        assert "Search backend unreachable" in response.json()["detail"]

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_search_history_no_user(search_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.routes.search.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id:
        mock_get_id.return_value = None
        response = await search_client.get("/api/v1/search/history")
        assert response.status_code == 404
        assert "detail" in response.json()

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_orchestrate_search_errors(search_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()
    from app.middleware.rate_limit import rate_limit
    app.dependency_overrides[rate_limit] = lambda: None

    with patch("app.routes.search.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.search.orchestrate_search", new_callable=AsyncMock) as mock_orch:

        mock_get_id.return_value = 1

        # Test HTTPStatusError
        mock_orch.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock(status_code=500))
        response = await search_client.get("/api/v1/search/orchestrate?q=test&backends=wikipedia")
        assert response.status_code == 502

        # Test RequestError
        mock_orch.side_effect = httpx.RequestError("Unreachable")
        response = await search_client.get("/api/v1/search/orchestrate?q=test&backends=wikipedia")
        assert response.status_code == 502

    app.dependency_overrides = {}
