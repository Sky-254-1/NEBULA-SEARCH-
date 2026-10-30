"""Authorization regressions for document indexing routes."""

import pytest

from app.indexing.progress import progress_tracker


@pytest.mark.asyncio
async def test_indexing_start_requires_document_ownership(client, auth_headers):
    owner_email = "index-owner@example.com"
    owner_password = "OwnerPass1!"
    assert (await client.post(
        "/api/v1/auth/signup",
        json={"email": owner_email, "password": owner_password},
    )).status_code == 201
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": owner_password},
    )
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    uploaded = await client.post(
        "/api/v1/documents/",
        headers=owner_headers,
        files={"file": ("owned.txt", b"indexable text", "text/plain")},
    )
    assert uploaded.status_code == 201
    document_id = uploaded.json()["id"]

    response = await client.post(
        "/api/v1/indexing/start",
        headers=auth_headers,
        json={"document_id": document_id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_indexing_jobs_are_private_to_the_submitter(client, auth_headers):
    from app.database import connect
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email("test@example.com")
    finally:
        await db.close()

    job_id = "private-indexing-job"
    progress_tracker.create(job_id, user_id=user_id, document_id=1)
    try:
        response = await client.get(
            f"/api/v1/indexing/job/{job_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        stranger_signup = await client.post(
            "/api/v1/auth/signup",
            json={"email": "index-stranger@example.com", "password": "StrangerPass1!"},
        )
        assert stranger_signup.status_code == 201
        stranger_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "index-stranger@example.com", "password": "StrangerPass1!"},
        )
        stranger_headers = {"Authorization": f"Bearer {stranger_login.json()['access_token']}"}

        response = await client.get(
            f"/api/v1/indexing/job/{job_id}",
            headers=stranger_headers,
        )
        assert response.status_code == 404
        response = await client.post(
            f"/api/v1/indexing/cancel/{job_id}",
            headers=stranger_headers,
        )
        assert response.status_code == 404
    finally:
        progress_tracker.remove(job_id)


@pytest.mark.asyncio
async def test_indexing_operational_routes_require_admin(client, auth_headers):
    for method, path in (
        ("get", "/api/v1/indexing/workers"),
        ("get", "/api/v1/indexing/metrics"),
        ("get", "/api/v1/indexing/scheduler"),
        ("get", "/api/v1/indexing/deadletter"),
    ):
        response = await getattr(client, method)(path, headers=auth_headers)
        assert response.status_code == 403, path
