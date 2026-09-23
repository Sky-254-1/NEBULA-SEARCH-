"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_and_login(client: AsyncClient):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "Password1!"},
    )
    assert signup.status_code == 201

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Password1!"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_duplicate_signup(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "Password1!"}
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 201
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 409


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "valid@example.com", "password": "Password1!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "valid@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_email(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_signup_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "password1"},
    )
    assert response.status_code == 422
