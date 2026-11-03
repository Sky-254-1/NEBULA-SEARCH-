"""API response, pagination, and OpenAPI contract regressions."""

import pytest


@pytest.mark.asyncio
async def test_validation_error_uses_stable_error_schema_and_request_id(client):
    response = await client.get("/api/v1/documents/")

    assert response.status_code == 401
    unauthorized = response.json()
    assert unauthorized["error_code"] == "UNAUTHORIZED"
    assert unauthorized["status"] == "error"
    assert unauthorized["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_invalid_pagination_returns_field_errors(client, auth_headers):
    response = await client.get(
        "/api/v1/documents/?page=0",
        headers=auth_headers,
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["validation_errors"]
    assert body["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_document_pagination_boundaries_and_total(client, auth_headers):
    from app.database import connect
    from app.database.repositories.document import DocumentRepository
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email("test@example.com")
        repo = DocumentRepository(db)
        for index in range(3):
            await repo.create(
                user_id,
                f"page-{index}.txt",
                "text/plain",
                f"/tmp/page-{index}.txt",
            )
    finally:
        await db.close()

    first = await client.get(
        "/api/v1/documents/?page=1&page_size=2", headers=auth_headers
    )
    second = await client.get(
        "/api/v1/documents/?page=2&page_size=2", headers=auth_headers
    )
    empty = await client.get(
        "/api/v1/documents/?page=3&page_size=2", headers=auth_headers
    )

    assert len(first.json()["documents"]) == 2
    assert first.json()["pagination"] == {
        "total": 3,
        "page": 1,
        "page_size": 2,
        "total_pages": 2,
        "has_next": True,
        "has_previous": False,
    }
    assert len(second.json()["documents"]) == 1
    assert second.json()["pagination"]["has_next"] is False
    assert second.json()["pagination"]["has_previous"] is True
    assert empty.json()["documents"] == []


@pytest.mark.asyncio
async def test_notification_pagination_uses_database_total_and_offset(client, auth_headers):
    from app.database import connect
    from app.database.repositories.user import UserRepository
    from app.database.repositories.notification import NotificationRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email("test@example.com")
        repo = NotificationRepository(db)
        for index in range(3):
            await repo.create(
                user_id,
                "system",
                "system",
                f"Notice {index}",
                "Test notification",
            )
    finally:
        await db.close()

    page_one = await client.get(
        "/api/v1/notifications/?page=1&page_size=2", headers=auth_headers
    )
    page_two = await client.get(
        "/api/v1/notifications/?page=2&page_size=2", headers=auth_headers
    )
    assert page_one.status_code == page_two.status_code == 200
    assert len(page_one.json()["notifications"]) == 2
    assert page_one.json()["pagination"]["total"] == 3
    assert page_one.json()["pagination"]["has_next"] is True
    assert len(page_two.json()["notifications"]) == 1
    assert page_two.json()["pagination"]["has_next"] is False


@pytest.mark.asyncio
async def test_openapi_versions_error_schema_and_route_security(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["version"] == "1.1.0"
    assert spec["info"]["x-api-version"] == "1.1.0"
    assert spec["info"]["x-api-route-versions"] == ["v1", "v2"]
    assert "APIError" in spec["components"]["schemas"]
    error_items = spec["components"]["schemas"]["APIError"]["properties"]["validation_errors"]["items"]
    assert error_items["$ref"] == "#/components/schemas/ValidationErrorDetail"
    assert "ValidationErrorDetail" in spec["components"]["schemas"]
    assert "BearerAuth" in spec["components"]["securitySchemes"]
    assert spec["paths"]["/api/v1/documents/"]["get"]["security"] == [
        {"BearerAuth": []}
    ]
    assert "default" in spec["paths"]["/api/v1/documents/"]["get"]["responses"]
    accepted = spec["paths"]["/api/v1/indexing/jobs"]["post"]["responses"]["202"]
    assert accepted["headers"]["Location"]["schema"]["type"] == "string"
    assert "security" not in spec["paths"]["/health"]["get"]
