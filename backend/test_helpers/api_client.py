"""HTTP client helpers for backend integration tests."""

from httpx import AsyncClient


async def login(client: AsyncClient, email: str, password: str) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    data = resp.json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "refresh_token": data.get("refresh_token"),
    }


async def signup_and_login(client: AsyncClient, email: str, password: str) -> dict:
    await client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    return await login(client, email, password)
