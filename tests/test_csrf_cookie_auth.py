"""Cookie-backed requests remain CSRF protected even with a bearer header."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bearer_header_does_not_bypass_csrf_when_cookies_are_present(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": "Bearer not-used-by-this-route",
            "Cookie": "csrf_token=csrf-value",
        },
        json={},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_matching_double_submit_token_allows_cookie_request(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": "Bearer not-used-by-this-route",
            "X-CSRF-Token": "csrf-value",
            "Cookie": "csrf_token=csrf-value",
        },
        json={},
    )
    assert response.status_code == 200
