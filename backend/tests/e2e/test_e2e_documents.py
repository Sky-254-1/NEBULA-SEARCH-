"""E2E tests — document upload and management flow."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_upload_list_delete_cycle(e2e_client: AsyncClient, e2e_auth: dict):
    """Full lifecycle: upload → list → delete."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    # Upload
    upload_resp = await e2e_client.post(
        "/api/v1/documents/",
        headers=headers,
        files={"file": ("e2e_test.txt", b"E2E test content for Nebula Search.", "text/plain")},
    )
    assert upload_resp.status_code == 200
    doc = upload_resp.json()
    doc_id = doc["id"]
    assert doc["filename"] == "e2e_test.txt"

    # List — new document appears
    list_resp = await e2e_client.get("/api/v1/documents/", headers=headers)
    assert list_resp.status_code == 200
    ids = [d["id"] for d in list_resp.json()["documents"]]
    assert doc_id in ids

    # Delete
    del_resp = await e2e_client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 200

    # Confirm gone
    list_resp2 = await e2e_client.get("/api/v1/documents/", headers=headers)
    ids_after = [d["id"] for d in list_resp2.json()["documents"]]
    assert doc_id not in ids_after


@pytest.mark.asyncio
async def test_upload_multiple_types(e2e_client: AsyncClient, e2e_auth: dict):
    """Multiple allowed file types can be uploaded."""
    headers = {"Authorization": e2e_auth["Authorization"]}
    test_files = [
        ("doc.md", b"# Markdown", "text/markdown"),
        ("data.csv", b"col1,col2\n1,2", "text/csv"),
        ("info.json", b'{"key":"val"}', "application/json"),
    ]
    for fname, content, ct in test_files:
        resp = await e2e_client.post(
            "/api/v1/documents/",
            headers=headers,
            files={"file": (fname, content, ct)},
        )
        assert resp.status_code == 200, f"Failed for {fname}: {resp.text}"


@pytest.mark.asyncio
async def test_upload_disallowed_type_rejected(e2e_client: AsyncClient, e2e_auth: dict):
    """Disallowed file types are rejected with 400."""
    headers = {"Authorization": e2e_auth["Authorization"]}
    resp = await e2e_client.post(
        "/api/v1/documents/",
        headers=headers,
        files={"file": ("script.sh", b"#!/bin/bash\necho hi", "text/x-shellscript")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_requires_auth(e2e_client: AsyncClient):
    """Unauthenticated upload returns 401."""
    resp = await e2e_client.post(
        "/api/v1/documents/",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_document_pagination(e2e_client: AsyncClient, e2e_auth: dict):
    """Pagination metadata is included in document list."""
    headers = {"Authorization": e2e_auth["Authorization"]}

    resp = await e2e_client.get("/api/v1/documents/?page=1&page_size=5", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "documents" in body
    if "pagination" in body and body["pagination"]:
        assert "total" in body["pagination"]
        assert "page" in body["pagination"]
