"""OAuth routes must not create or link identities without provider validation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unverified_oauth_routes_fail_closed(client: AsyncClient, auth_headers: dict):
    authorize = await client.get("/api/v1/auth/oauth/google/authorize")
    assert authorize.status_code == 501

    callback = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "untrusted", "state": "untrusted"},
    )
    assert callback.status_code == 501

    link_without_auth = await client.post(
        "/api/v1/auth/oauth/link",
        params={"provider": "google", "code": "untrusted"},
    )
    assert link_without_auth.status_code == 401

    link = await client.post(
        "/api/v1/auth/oauth/link",
        params={"provider": "google", "code": "untrusted"},
        headers=auth_headers,
    )
    assert link.status_code == 501

    accounts = await client.get("/api/v1/auth/oauth/accounts", headers=auth_headers)
    assert accounts.status_code == 501

    unlink = await client.delete(
        "/api/v1/auth/oauth/unlink",
        params={"provider": "google"},
        headers=auth_headers,
    )
    assert unlink.status_code == 501
