"""Vector indexing and search tests."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "test_vector.db")
os.environ.setdefault("JWT_SECRET", "vector-test-secret")
os.environ.setdefault("APP_ENV", "testing")

from app.config import get_settings
from app.database import init_db
from app.main import app

get_settings.cache_clear()


@pytest_asyncio.fixture
async def vector_client():
    db_path = get_settings().db_path
    if os.path.exists(db_path):
        os.remove(db_path)
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest_asyncio.fixture
async def vector_auth(vector_client: AsyncClient):
    await vector_client.post(
        "/api/v1/auth/signup",
        json={"email": "vector@test.com", "password": "SecurePass1!"},
    )
    login = await vector_client.post(
        "/api/v1/auth/login",
        json={"email": "vector@test.com", "password": "SecurePass1!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_vector_upload_index_search(vector_client, vector_auth):
    content = b"Nebula hybrid vector search test content for pytest."
    files = {"file": ("vec-test.txt", content, "text/plain")}
    upload = await vector_client.post(
        "/api/v1/storage/documents",
        headers=vector_auth,
        files=files,
    )
    assert upload.status_code == 200
    doc_id = upload.json()["id"]

    index = await vector_client.post(
        f"/api/v1/vector/documents/{doc_id}/index-now",
        headers=vector_auth,
    )
    assert index.status_code == 200

    search = await vector_client.post(
        "/api/v1/vector/search",
        headers=vector_auth,
        json={"query": "hybrid vector search", "top_k": 5},
    )
    assert search.status_code == 200
    body = search.json()
    assert body["total"] > 0


@pytest.mark.asyncio
async def test_chunking_module():
    from vector.chunking import chunk_text

    text = "word " * 200
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1


@pytest.mark.asyncio
async def test_hash_embedding():
    from vector.embeddings import embed_text

    vec, model, dims = await embed_text("test embedding", model="local-hash")
    assert model == "local-hash"
    assert len(vec) == dims
