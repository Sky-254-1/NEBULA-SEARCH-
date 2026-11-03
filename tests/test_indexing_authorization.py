"""Authorization regressions for document indexing routes."""

import uuid

import pytest

from app.indexing.progress import progress_tracker


@pytest.mark.asyncio
async def test_indexing_start_requires_document_ownership(client, auth_headers):
    from app.indexing.queue import indexing_queue

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

    own_upload = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("own.txt", b"own text", "text/plain")},
    )
    assert own_upload.status_code == 201
    queue_size_before = indexing_queue.size

    response = await client.post(
        "/api/v1/indexing/start",
        headers=auth_headers,
        json={"document_id": document_id},
    )
    assert response.status_code == 404

    # A mixed batch is rejected before any of its accessible documents are
    # enqueued, avoiding partial reindex side effects.
    response = await client.post(
        "/api/v1/indexing/reindex",
        headers=auth_headers,
        json={"document_ids": [own_upload.json()["id"], document_id]},
    )
    assert response.status_code == 404
    assert indexing_queue.size == queue_size_before


@pytest.mark.asyncio
async def test_indexing_start_persists_job_owner(client, auth_headers):
    from app.database import connect
    from app.database.repositories.indexing_job import IndexingJobRepository
    from app.database.repositories.user import UserRepository
    from app.indexing.queue import indexing_queue

    uploaded = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("persisted.txt", b"indexable text", "text/plain")},
    )
    assert uploaded.status_code == 201
    document_id = uploaded.json()["id"]
    started = await client.post(
        "/api/v1/indexing/start",
        headers=auth_headers,
        json={"document_id": document_id},
    )
    assert started.status_code == 200
    job_id = started.json()["data"]["job_id"]

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email("test@example.com")
        record = await IndexingJobRepository(db).get_for_user(job_id, user_id)
        assert record["document_id"] == document_id
        assert record["status"] == "QUEUED"
    finally:
        await db.close()
        await indexing_queue.remove(job_id)
        progress_tracker.remove(job_id)


@pytest.mark.asyncio
async def test_indexing_job_resource_aliases_return_accepted_and_owner_status(
    client, auth_headers
):
    from app.indexing.progress import progress_tracker
    from app.indexing.queue import indexing_queue

    upload = await client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("resource.txt", b"index me", "text/plain")},
    )
    assert upload.status_code == 201

    created = await client.post(
        "/api/v1/indexing/jobs",
        headers=auth_headers,
        json={"document_id": upload.json()["id"]},
    )
    assert created.status_code == 202
    job_id = created.json()["data"]["job_id"]
    assert created.headers["Location"] == f"/api/v1/indexing/jobs/{job_id}"

    fetched = await client.get(
        f"/api/v1/indexing/jobs/{job_id}", headers=auth_headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["data"]["job_id"] == job_id

    try:
        assert await indexing_queue.remove(job_id)
    finally:
        progress_tracker.remove(job_id)


@pytest.mark.asyncio
async def test_indexing_jobs_are_private_to_the_submitter(client, auth_headers):
    from app.database import connect
    from app.database.repositories.document import DocumentRepository
    from app.database.repositories.indexing_job import IndexingJobRepository
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email("test@example.com")
        document_id = await DocumentRepository(db).create(
            user_id, "private.txt", "text/plain", "/tmp/private.txt"
        )
        await IndexingJobRepository(db).create(
            "private-indexing-job", user_id, document_id, "private.txt"
        )
    finally:
        await db.close()

    job_id = "private-indexing-job"
    progress_tracker.create(job_id, user_id=user_id, document_id=document_id)
    try:
        # Ownership is durable and the in-memory progress record may be rebuilt.
        progress_tracker.remove(job_id)
        response = await client.get(
            f"/api/v1/indexing/job/{job_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        listed = await client.get("/api/v1/indexing/jobs", headers=auth_headers)
        assert listed.status_code == 200
        assert any(job["job_id"] == job_id for job in listed.json()["data"]["jobs"])

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


async def _create_retry_job(email: str, status: str, error: str = "temporary error") -> str:
    from app.database import connect
    from app.database.repositories.document import DocumentRepository
    from app.database.repositories.indexing_job import IndexingJobRepository
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email(email)
        document_id = await DocumentRepository(db).create(
            user_id, "retry.txt", "text/plain", "/tmp/retry.txt"
        )
        job_id = f"retry-{uuid.uuid4()}"
        jobs = IndexingJobRepository(db)
        await jobs.create(job_id, user_id, document_id, "retry.txt")
        await db.execute(
            "UPDATE index_jobs SET status = ?, error_message = ? WHERE job_id = ?",
            (status, error, job_id),
        )
        await db.commit()
        return job_id
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_retry_queues_failed_owned_job(client, auth_headers):
    from app.database import connect
    from app.database.repositories.indexing_job import IndexingJobRepository
    from app.database.repositories.user import UserRepository
    from app.indexing.progress import progress_tracker
    from app.indexing.queue import indexing_queue

    job_id = await _create_retry_job("test@example.com", "FAILED")
    try:
        response = await client.post(
            f"/api/v1/indexing/retry/{job_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "QUEUED"
        assert any(job["job_id"] == job_id for job in await indexing_queue.peek(100))

        db = await connect()
        try:
            user_id = await UserRepository(db).get_id_by_email("test@example.com")
            record = await IndexingJobRepository(db).get_for_user(job_id, user_id)
            assert record["status"] == "QUEUED"
            assert record["retry_count"] == 1
        finally:
            await db.close()
    finally:
        await indexing_queue.remove(job_id)
        progress_tracker.remove(job_id)


@pytest.mark.asyncio
async def test_retry_missing_job_returns_404(client, auth_headers):
    response = await client.post(
        "/api/v1/indexing/retry/missing-job", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_is_owner_scoped(client, auth_headers):
    job_id = await _create_retry_job("test@example.com", "FAILED")
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "retry-stranger@example.com", "password": "Password1!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "retry-stranger@example.com", "password": "Password1!"},
    )
    stranger_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.post(
        f"/api/v1/indexing/retry/{job_id}", headers=stranger_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_rejects_completed_job_and_nonretryable_failure(client, auth_headers):
    completed_job = await _create_retry_job("test@example.com", "COMPLETED")
    response = await client.post(
        f"/api/v1/indexing/retry/{completed_job}", headers=auth_headers
    )
    assert response.status_code == 409

    invalid_job = await _create_retry_job(
        "test@example.com", "FAILED", error="unsupported file format"
    )
    response = await client.post(
        f"/api/v1/indexing/retry/{invalid_job}", headers=auth_headers
    )
    assert response.status_code == 409
