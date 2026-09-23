"""Refresh token auth tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_returns_refresh_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "refresh@example.com", "password": "Password1!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password1!"},
    )
    data = login.json()
    assert login.status_code == 200
    assert data.get("refresh_token")


@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "flow@example.com", "password": "Password1!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "Password1!"},
    )
    refresh_token = login.json()["refresh_token"]
    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
