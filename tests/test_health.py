"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


# Note: Root endpoint test removed due to API versioning middleware
# The API requires versioned paths (/api/v1/ or /api/v2/)
# Health endpoint is tested separately in test_health()


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "testing"
    assert data["database"] == "sqlite"
    assert data["cache"] in {"memory", "redis"}
