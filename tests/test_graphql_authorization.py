"""GraphQL owner identity cannot be selected by the caller."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_graphql_search_history_requires_authenticated_user(client: AsyncClient):
    response = await client.post(
        "/graphql/",
        json={"query": "{ searchHistory { id query } }"},
    )
    assert response.status_code == 200
    # The field is non-null in the schema, so GraphQL propagates the resolver
    # authorization error to the root `data` value.
    assert response.json()["data"] is None
    assert response.json()["errors"]


@pytest.mark.asyncio
async def test_graphql_cannot_read_or_write_another_users_history(
    client: AsyncClient, auth_headers: dict[str, str]
):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "graphql-other@example.com", "password": "Password1!"},
    )
    assert signup.status_code == 201
    from app.database import connect
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        other_id = await UserRepository(db).get_id_by_email("graphql-other@example.com")
    finally:
        await db.close()

    query = await client.post(
        "/graphql/",
        headers=auth_headers,
        json={"query": f'{{ searchHistory(userId: "{other_id}") {{ id }} }}'},
    )
    assert query.status_code == 200
    assert query.json()["data"] is None
    assert query.json()["errors"]

    mutation = await client.post(
        "/graphql/",
        headers=auth_headers,
        json={
            "query": (
                'mutation { saveSearch(query: "spoof", resultsCount: 1, '
                f'userId: "{other_id}") {{ id }} }}'
            )
        },
    )
    assert mutation.status_code == 200
    assert mutation.json()["data"] is None
    assert mutation.json()["errors"]
