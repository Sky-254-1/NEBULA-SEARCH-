"""Route-level upload rollback and validation tests."""

import pytest

from app.services.queue import job_queue


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("upload_path", "list_path"),
    [
        ("/api/v1/documents/", "/api/v1/documents/"),
        ("/api/v1/storage/documents", "/api/v1/storage/documents"),
    ],
)
async def test_upload_rolls_back_when_enqueue_fails(
    async_client, auth_headers, monkeypatch, upload_path, list_path
):
    async def fail_enqueue(*args, **kwargs):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(job_queue, "enqueue", fail_enqueue)

    resp = await async_client.post(
        upload_path,
        headers=auth_headers,
        files={"file": ("rollback.txt", b"rollback me", "text/plain")},
    )
    assert resp.status_code == 503

    listing = await async_client.get(list_path, headers=auth_headers)
    assert listing.status_code == 200
    filenames = [doc["filename"] for doc in listing.json()["documents"]]
    assert "rollback.txt" not in filenames


@pytest.mark.asyncio
async def test_upload_rejects_invalid_pdf_signature(async_client, auth_headers):
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("fake.pdf", b"definitely not a pdf", "application/pdf")},
    )
    assert resp.status_code == 400
