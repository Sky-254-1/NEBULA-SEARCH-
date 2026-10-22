"""Extended tests for Vector routes."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture
async def vector_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_vector_status_not_found(vector_client):
    with patch("app.routes.vector.get_current_user", return_value="test@example.com"), \
         patch("app.routes.vector.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.vector.DocumentRepository.get_by_id", new_callable=AsyncMock) as mock_get_doc, \
         patch("app.routes.vector.Depends", side_effect=lambda x: x): # Bypass Depends

        mock_get_id.return_value = 1
        mock_get_doc.return_value = None

        # We need to bypass the actual dependency injection in FastAPI.
        # Another way is to override app.dependency_overrides.
        from app.services.auth import get_current_user
        from app.database import get_db

        app.dependency_overrides[get_current_user] = lambda: "test@example.com"
        app.dependency_overrides[get_db] = lambda: MagicMock()

        try:
            response = await vector_client.get("/api/v1/vector/documents/999/status")
            assert response.status_code == 404
        finally:
            app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_vector_reindex_all(vector_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.routes.vector.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.vector.DocumentRepository.list_for_user", new_callable=AsyncMock) as mock_list, \
         patch("app.routes.vector.job_queue.enqueue", new_callable=AsyncMock) as mock_enqueue:

        mock_get_id.return_value = 1
        mock_list.return_value = [{"id": 1}, {"id": 2}]

        try:
            response = await vector_client.post("/api/v1/vector/documents/reindex-all", json={"limit": 10})
            assert response.status_code == 200
            assert response.json()["count"] == 2
            assert mock_enqueue.call_count == 2
        finally:
            app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_vector_stats(vector_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.routes.vector.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.vector.ChunkRepository.list_for_user", new_callable=AsyncMock) as mock_list:

        mock_get_id.return_value = 1
        mock_list.return_value = [{"document_id": 1}, {"document_id": 1}, {"document_id": 2}]

        try:
            response = await vector_client.get("/api/v1/vector/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["chunks"] == 3
            assert data["documents_indexed"] == 2
        finally:
            app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_vector_export(vector_client):
    from app.services.auth import get_current_user
    from app.database import get_db
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.routes.vector.UserRepository.get_id_by_email", new_callable=AsyncMock) as mock_get_id, \
         patch("app.routes.vector.ChunkRepository.list_for_user", new_callable=AsyncMock) as mock_list, \
         patch("app.routes.vector.ExportRepository.create", new_callable=AsyncMock) as mock_create, \
         patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_text"):

        mock_get_id.return_value = 1
        mock_list.return_value = [{"id": 1}]
        mock_create.return_value = 101

        try:
            response = await vector_client.post("/api/v1/vector/export")
            assert response.status_code == 200
            assert response.json()["export_id"] == 101
        finally:
            app.dependency_overrides = {}
