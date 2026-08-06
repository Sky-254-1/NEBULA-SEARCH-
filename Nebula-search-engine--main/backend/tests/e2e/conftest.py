"""E2E test configuration — requires a live PostgreSQL + Redis stack."""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# E2E tests use the real Postgres/Redis configured via environment
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_key_min_32_chars_long!!")

from app.main import app
from app.database import init_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_e2e_db():
    """Initialise the database once for the full E2E suite."""
    await init_db()
    yield


@pytest_asyncio.fixture
async def e2e_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def e2e_auth(e2e_client: AsyncClient):
    """Register and login a fresh E2E user, return auth headers."""
    import uuid
    email = f"e2e_{uuid.uuid4().hex[:8]}@nebula.dev"
    password = "E2ePassword1!"

    await e2e_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password},
    )
    login = await e2e_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login.json()
    token = data.get("access_token")
    return {"Authorization": f"Bearer {token}", "email": email, "password": password}
