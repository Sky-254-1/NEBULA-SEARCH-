"""Storage API endpoint tests."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_settings_get_and_update(client: AsyncClient, auth_headers: dict):
    get_res = await client.get("/api/v1/storage/settings", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["settings"] == {}

    put_res = await client.put(
        "/api/v1/storage/settings",
        headers=auth_headers,
        json={"settings": {"theme": "dark", "backends": "wikipedia"}},
    )
    assert put_res.status_code == 200
    assert put_res.json()["settings"]["theme"] == "dark"


@pytest.mark.asyncio
async def test_document_upload_and_list(client: AsyncClient, auth_headers: dict):
    content = b"Nebula test document content"
    files = {"file": ("notes.txt", io.BytesIO(content), "text/plain")}
    upload = await client.post(
        "/api/v1/storage/documents",
        headers=auth_headers,
        files=files,
    )
    assert upload.status_code == 200
    doc_id = upload.json()["id"]

    listing = await client.get("/api/v1/storage/documents", headers=auth_headers)
    assert listing.status_code == 200
    docs = listing.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    deleted = await client.delete(f"/api/v1/storage/documents/{doc_id}", headers=auth_headers)
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_export_create_and_list(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/api/v1/storage/exports",
        headers=auth_headers,
        json={"export_type": "search_history", "data": {"queries": ["test"]}},
    )
    assert create.status_code == 200
    export_id = create.json()["id"]

    listing = await client.get("/api/v1/storage/exports", headers=auth_headers)
    assert listing.status_code == 200
    exports = listing.json()["exports"]
    assert any(e["id"] == export_id for e in exports)


@pytest.mark.asyncio
async def test_storage_requires_auth(client: AsyncClient):
    assert (await client.get("/api/v1/storage/settings")).status_code == 401
