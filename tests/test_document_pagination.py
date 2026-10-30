"""Document pages use database limits and remain scoped to their owner."""

import pytest
from httpx import AsyncClient

from app.database.engine import connect
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_document_pagination_counts_and_returns_only_current_users_documents(
    client: AsyncClient, auth_headers: dict[str, str]
):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "pagination-other@example.com", "password": "Password1!"},
    )
    assert signup.status_code in (201, 200)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "pagination-other@example.com", "password": "Password1!"},
    )
    assert login.status_code == 200
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    db = await connect()
    try:
        users = UserRepository(db)
        owner_id = await users.get_id_by_email("test@example.com")
        other_id = await users.get_id_by_email("pagination-other@example.com")
        assert owner_id and other_id
        documents = DocumentRepository(db)
        for index in range(61):
            await documents.create(
                owner_id, f"owner-{index}.txt", "text/plain", f"/tmp/owner-{index}"
            )
        for index in range(3):
            await documents.create(
                other_id, f"other-{index}.txt", "text/plain", f"/tmp/other-{index}"
            )
    finally:
        await db.close()

    first = await client.get(
        "/api/v1/documents/?page=1&page_size=20", headers=auth_headers
    )
    fourth = await client.get(
        "/api/v1/documents/?page=4&page_size=20", headers=auth_headers
    )
    other = await client.get(
        "/api/v1/documents/?page=1&page_size=20", headers=other_headers
    )

    assert first.status_code == fourth.status_code == other.status_code == 200
    first_data, fourth_data, other_data = first.json(), fourth.json(), other.json()
    assert first_data["pagination"] == {
        "total": 61,
        "page": 1,
        "page_size": 20,
        "total_pages": 4,
        "has_next": True,
        "has_previous": False,
    }
    assert len(first_data["documents"]) == 20
    assert len(fourth_data["documents"]) == 1
    assert other_data["pagination"]["total"] == 3
    assert len(other_data["documents"]) == 3
    assert not (
        {doc["id"] for doc in first_data["documents"] + fourth_data["documents"]}
        & {doc["id"] for doc in other_data["documents"]}
    )
