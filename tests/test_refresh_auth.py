"""Refresh token auth tests."""

import asyncio

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


@pytest.mark.asyncio
async def test_concurrent_refresh_reuse_revokes_the_entire_token_family(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "concurrent-refresh@example.com", "password": "Password1!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "concurrent-refresh@example.com", "password": "Password1!"},
    )
    original = login.json()["refresh_token"]

    first, second = await asyncio.gather(
        client.post("/api/v1/auth/refresh", json={"refresh_token": original}),
        client.post("/api/v1/auth/refresh", json={"refresh_token": original}),
    )
    assert sorted((first.status_code, second.status_code)) == [200, 401]

    winner = first if first.status_code == 200 else second
    descendant = winner.json()["refresh_token"]
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": descendant})
    assert reused.status_code == 401
