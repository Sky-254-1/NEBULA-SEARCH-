"""E2E test configuration — requires a live PostgreSQL + Redis stack."""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# E2E tests use the real Postgres/Redis configured via environment
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_key_min_32_chars_long!!")

# Ensure database path is consistent with root conftest
# Import settings first to get the correct db_path
from app.config import get_settings
settings = get_settings()

# Set DATABASE_URL if not already set for e2e tests
if "DATABASE_URL" not in os.environ:
    import tempfile
    from pathlib import Path
    _TEST_DB_DIR = Path(tempfile.gettempdir()) / "nebula-pytest"
    _TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    _TEST_DB_PATH = _TEST_DB_DIR / f"test_e2e_{os.getpid()}.db"
    os.environ["DATABASE_URL"] = str(_TEST_DB_PATH)

from app.main import app
from app.database import init_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_e2e_db():
    """Initialise the database once for the full E2E suite."""
    await init_db()
    yield


@pytest_asyncio.fixture
async def e2e_client():
    """Create a fresh e2e client for each test to ensure isolation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def e2e_auth(e2e_client: AsyncClient):
    """Register and login a fresh E2E user, return auth headers.
    
    Each test gets a fresh user with a unique UUID email to avoid conflicts.
    """
    import uuid
    email = f"e2e_{uuid.uuid4().hex[:8]}@nebula.dev"
    password = "E2ePassword1!"

    # Signup
    resp = await e2e_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201, f"Signup failed: {resp.status_code} - {resp.text}"
    
    # Login
    login = await e2e_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, f"Login failed: {login.status_code} - {login.text}"
    
    data = login.json()
    token = data.get("access_token")
    assert token, "Login response missing access_token"
    
    return {"Authorization": f"Bearer {token}", "email": email, "password": password}
