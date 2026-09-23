"""Pytest configuration and shared fixtures for backend tests."""

import gc
import os
import sys
import tempfile
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Unique SQLite path per test process — avoids Windows file-lock collisions between runs.
_TEST_DB_DIR = Path(tempfile.gettempdir()) / "nebula-pytest"
_TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
_TEST_DB_PATH = _TEST_DB_DIR / f"test_{os.getpid()}.db"

os.environ["DATABASE_URL"] = str(_TEST_DB_PATH)
os.environ["JWT_SECRET"] = "test-secret-key-for-nebula-tests-only"
os.environ["APP_ENV"] = "testing"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["SIGNUP_RATE_LIMIT"] = "1000"
os.environ["LOGIN_RATE_LIMIT"] = "1000"
os.environ["REFRESH_RATE_LIMIT"] = "1000"

from app.config import get_settings
from app.database import init_db
from app.main import app

get_settings.cache_clear()


def pytest_sessionstart() -> None:
    get_settings.cache_clear()


def _close_db_connections() -> None:
    """Release pooled SQLite/PostgreSQL handles before deleting test DB files."""
    import asyncio

    async def _close() -> None:
        from app.database.engine import close_pool

        try:
            await close_pool()
        except Exception:
            pass

    try:
        asyncio.run(_close())
    except Exception:
        pass
    gc.collect()


def _safe_unlink_db(db_path: Path) -> None:
    """Remove test database file; tolerate Windows file locks."""
    if not db_path.exists():
        return
    _close_db_connections()
    for attempt in range(8):
        try:
            db_path.unlink()
            return
        except PermissionError:
            time.sleep(0.05 * (2**attempt))
    # Rename stale file so the next session starts clean.
    try:
        db_path.rename(db_path.with_suffix(f".db.stale.{os.getpid()}"))
    except OSError:
        pass


@pytest.fixture(scope="session", autouse=True)
def init_test_database() -> None:
    """Initialize SQLite schema once per test session."""
    import asyncio

    db_path = Path(get_settings().db_path)
    _safe_unlink_db(db_path)
    asyncio.run(init_db())
    yield
    _safe_unlink_db(db_path)


@pytest_asyncio.fixture
async def setup_db() -> AsyncGenerator[None, None]:
    db_path = Path(get_settings().db_path)
    _safe_unlink_db(db_path)
    await init_db()
    yield
    _safe_unlink_db(db_path)


@pytest.fixture(scope="module")
def client():
    """Synchronous TestClient with proper lifespan teardown."""
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient) -> dict[str, str]:
    await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "Password1!"},
    )
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Password1!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
