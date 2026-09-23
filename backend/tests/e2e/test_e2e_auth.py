"""E2E tests — complete authentication flow."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_login_refresh_logout(e2e_client: AsyncClient):
    """Full auth lifecycle: signup → login → refresh → logout."""
    email = f"e2e_{uuid.uuid4().hex[:8]}@nebula.dev"
    password = "StrongPass1!"

    # 1. Signup
    resp = await e2e_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201
    assert "message" in resp.json()

    # 2. Login
    resp = await e2e_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    # 3. /me with valid token
    resp = await e2e_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == email

    # 4. Refresh
    resp = await e2e_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens

    # 5. Logout
    resp = await e2e_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_signup_rejected(e2e_client: AsyncClient):
    """Signing up with the same email twice returns 409."""
    email = f"dup_{uuid.uuid4().hex[:8]}@nebula.dev"
    password = "DupPass1!"

    # First signup succeeds
    resp1 = await e2e_client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert resp1.status_code == 201
    
    # Second signup with same email should return 409
    resp2 = await e2e_client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(e2e_client: AsyncClient):
    """Wrong password returns 401."""
    email = f"wp_{uuid.uuid4().hex[:8]}@nebula.dev"
    await e2e_client.post("/api/v1/auth/signup", json={"email": email, "password": "Correct1!"})

    resp = await e2e_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass1!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_rejected(e2e_client: AsyncClient):
    """Weak password is rejected at signup."""
    resp = await e2e_client.post(
        "/api/v1/auth/signup",
        json={"email": f"weak_{uuid.uuid4().hex[:8]}@test.com", "password": "weakpass"},  # 8 chars but no uppercase, digit, or special char
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_me_without_token_returns_401(e2e_client: AsyncClient):
    """/me without token returns 401."""
    resp = await e2e_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_reuse_rejected(e2e_client: AsyncClient):
    """Reusing a refresh token after rotation is rejected."""
    email = f"reuse_{uuid.uuid4().hex[:8]}@nebula.dev"
    await e2e_client.post("/api/v1/auth/signup", json={"email": email, "password": "Reuse1Pass!"})
    login = await e2e_client.post("/api/v1/auth/login", json={"email": email, "password": "Reuse1Pass!"})
    original_refresh = login.json()["refresh_token"]

    # Rotate the token
    await e2e_client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})

    # Try to reuse the original token
    resp = await e2e_client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert resp.status_code == 401
