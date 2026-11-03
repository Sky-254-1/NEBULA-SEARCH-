"""Tests for the documents domain routes."""

import io
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_documents_requires_auth(async_client: AsyncClient):
    """Documents list requires authentication."""
    resp = await async_client.get("/api/v1/documents/")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_documents_authenticated(async_client: AsyncClient, auth_headers: dict):
    """Authenticated user can list documents (empty initially)."""
    resp = await async_client.get("/api/v1/documents/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "documents" in body
    assert isinstance(body["documents"], list)


@pytest.mark.asyncio
async def test_upload_document_requires_auth(async_client: AsyncClient):
    """Upload endpoint requires authentication."""
    resp = await async_client.post(
        "/api/v1/documents/",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_upload_document_txt(async_client: AsyncClient, auth_headers: dict):
    """Upload a .txt file succeeds."""
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("hello.txt", b"Hello world content", "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["filename"] == "hello.txt"


@pytest.mark.asyncio
async def test_upload_document_invalid_extension(async_client: AsyncClient, auth_headers: dict):
    """Upload with disallowed extension is rejected."""
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("malware.exe", b"\x4d\x5a", "application/octet-stream")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_document_too_large(async_client: AsyncClient, auth_headers: dict):
    """File over 10MB is rejected."""
    large_content = b"x" * (10 * 1024 * 1024 + 1)
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("big.txt", large_content, "text/plain")},
    )
    # Accept either 413 (endpoint rejection) or 400 (test client size limit)
    assert resp.status_code in (400, 413)


@pytest.mark.asyncio
async def test_upload_markdown(async_client: AsyncClient, auth_headers: dict):
    """Upload a .md file succeeds."""
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("readme.md", b"# Hello\nWorld", "text/markdown")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "readme.md"


@pytest.mark.asyncio
async def test_upload_json(async_client: AsyncClient, auth_headers: dict):
    """Upload a .json file succeeds."""
    resp = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("data.json", b'{"key": "value"}', "application/json")},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_delete_document_not_found(async_client: AsyncClient, auth_headers: dict):
    """Deleting non-existent document returns 404."""
    resp = await async_client.delete("/api/v1/documents/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_then_delete(async_client: AsyncClient, auth_headers: dict):
    """Upload then delete a document successfully."""
    upload = await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("todelete.txt", b"Some content", "text/plain")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    delete = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert delete.status_code == 200
    assert "deleted" in delete.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_list_documents_shows_uploaded(async_client: AsyncClient, auth_headers: dict):
    """Uploaded document appears in list."""
    await async_client.post(
        "/api/v1/documents/",
        headers=auth_headers,
        files={"file": ("listed.txt", b"listing test", "text/plain")},
    )
    resp = await async_client.get("/api/v1/documents/", headers=auth_headers)
    assert resp.status_code == 200
    filenames = [d["filename"] for d in resp.json()["documents"]]
    assert "listed.txt" in filenames


@pytest.mark.asyncio
async def test_delete_other_users_document(async_client: AsyncClient, auth_headers: dict):
    """Cannot delete another user's document."""
    # Create a fresh second identity directly so MFA policy and account state
    # from other tests cannot turn an ownership regression into a skipped test.
    from app.database import connect
    from app.database.repositories.user import UserRepository
    from app.services.auth import create_access_token, hash_password

    other_email = f"other-{uuid.uuid4().hex}@example.com"
    db = await connect()
    try:
        users = UserRepository(db)
        await users.create(other_email, hash_password("OtherPass1!"))
    finally:
        await db.close()

    other_token = create_access_token(other_email, role="user")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    upload = await async_client.post(
        "/api/v1/documents/",
        headers=other_headers,
        files={"file": ("private.txt", b"private content", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["id"]

    # Original user tries to delete it
    delete = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert delete.status_code == 404
