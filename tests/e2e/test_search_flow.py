"""
Nebula Search Engine — E2E (End-to-End) Tests.
Tests complete user workflows across the entire application.

Prerequisites:
    - Backend running on http://localhost:8000
    - Frontend available (optional)
    - Database seeded with test data

Usage:
    pip install pytest httpx
    python -m pytest tests/e2e/ -v --base-url=http://localhost:8000
"""

import os
import uuid
import pytest
import httpx
from typing import Generator, Optional

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
TEST_EMAIL = f"e2e_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "E2eTest@123!Strong"


@pytest.fixture(scope="session")
def client() -> Generator:
    """HTTP client for E2E tests."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="module")
def user_token(client: httpx.Client) -> str:
    """Register and login a test user, return access token."""
    # Signup
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code in (201, 409), f"Signup failed: {resp.text}"
    
    # Login
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(user_token: str) -> dict:
    """Authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


# ============================================
# E2E Test: Authentication Flow
# ============================================

class TestAuthFlow:
    """Complete authentication lifecycle."""
    
    def test_health_check(self, client: httpx.Client):
        """Health endpoint should be accessible."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
    
    def test_unauthenticated_access(self, client: httpx.Client):
        """Unauthenticated requests should return 401."""
        resp = client.get("/api/v1/users/profile")
        assert resp.status_code == 401
    
    def test_login_validates_password(self, client: httpx.Client):
        """Login with invalid credentials."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrong"},
        )
        assert resp.status_code in (401, 423), f"Expected 401/423, got {resp.status_code}"
    
    def test_token_refresh(self, client: httpx.Client, user_token: str):
        """Refresh token should work."""
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # May return 200 or require a refresh token
        assert resp.status_code in (200, 422), f"Refresh failed: {resp.text}"


# ============================================
# E2E Test: Search Flow
# ============================================

class TestSearchFlow:
    """Complete search workflow."""
    
    def test_basic_search(self, client: httpx.Client, auth_headers: dict):
        """Basic search should return results."""
        resp = client.get(
            "/api/v1/search?q=test+search+query",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        data = resp.json()
        # May have results or empty
        assert "results" in data or "data" in data
    
    def test_search_with_pagination(self, client: httpx.Client, auth_headers: dict):
        """Search with pagination parameters."""
        resp = client.get(
            "/api/v1/search?q=python&page=1&page_size=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if "pagination" in data:
            assert data["pagination"]["page"] == 1
    
    def test_search_with_filters(self, client: httpx.Client, auth_headers: dict):
        """Search with filters."""
        resp = client.get(
            "/api/v1/search?q=data&type=web&sort=relevance",
            headers=auth_headers,
        )
        assert resp.status_code in (200, 422)
    
    def test_autocomplete(self, client: httpx.Client, auth_headers: dict):
        """Autocomplete should return suggestions."""
        resp = client.get(
            "/api/v1/autocomplete?q=py",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data or "results" in data
    
    def test_spell_correction(self, client: httpx.Client, auth_headers: dict):
        """Spell correction should suggest corrections."""
        resp = client.get(
            "/api/v1/spell/check?q=pyhton",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should suggest "python"
        suggestions = data.get("suggestions", data.get("corrections", []))
        assert len(suggestions) > 0 or "corrected" in data


# ============================================
# E2E Test: Document Management
# ============================================

class TestDocumentFlow:
    """Document upload, list, and delete workflow."""
    
    def test_list_documents_empty(self, client: httpx.Client, auth_headers: dict):
        """New users should have no documents."""
        resp = client.get("/api/v1/documents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        docs = data.get("documents", data.get("data", []))
        assert len(docs) == 0
    
    def test_upload_document(self, client: httpx.Client, auth_headers: dict):
        """Upload a valid document."""
        resp = client.post(
            "/api/v1/documents/",
            headers=auth_headers,
            files={"file": ("test.txt", b"Hello, World! This is a test document.", "text/plain")},
        )
        assert resp.status_code == 200, f"Upload failed: {resp.text}"
        data = resp.json()
        assert "id" in data
    
    def test_upload_invalid_type(self, client: httpx.Client, auth_headers: dict):
        """Uploading invalid file type should fail."""
        resp = client.post(
            "/api/v1/documents/",
            headers=auth_headers,
            files={"file": ("test.exe", b"fake binary", "application/octet-stream")},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    
    def test_list_documents_after_upload(self, client: httpx.Client, auth_headers: dict):
        """After upload, documents should appear."""
        resp = client.get("/api/v1/documents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        docs = data.get("documents", data.get("data", []))
        assert len(docs) > 0
    
    def test_delete_document(self, client: httpx.Client, auth_headers: dict):
        """Delete an existing document."""
        # First get a document ID
        resp = client.get("/api/v1/documents/", headers=auth_headers)
        docs = resp.json().get("documents", resp.json().get("data", []))
        if docs:
            doc_id = docs[0]["id"]
            resp = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
            assert resp.status_code == 200, f"Delete failed: {resp.text}"


# ============================================
# E2E Test: User Profile & Settings
# ============================================

class TestUserProfile:
    """User profile and settings workflow."""
    
    def test_get_profile(self, client: httpx.Client, auth_headers: dict):
        """Authenticated user can get profile."""
        resp = client.get("/api/v1/users/profile", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert data["email"] == TEST_EMAIL
    
    def test_update_profile(self, client: httpx.Client, auth_headers: dict):
        """User can update profile."""
        resp = client.put(
            "/api/v1/users/profile",
            headers=auth_headers,
            json={"name": "E2E Test User"},
        )
        assert resp.status_code in (200, 422), f"Update failed: {resp.text}"
    
    def test_get_preferences(self, client: httpx.Client, auth_headers: dict):
        """User can get preferences."""
        resp = client.get("/api/v1/users/preferences", headers=auth_headers)
        assert resp.status_code == 200


# ============================================
# E2E Test: Analytics & Metrics
# ============================================

class TestAnalytics:
    """Analytics and metrics endpoints."""
    
    def test_metrics_endpoint(self, client: httpx.Client):
        """Prometheus metrics endpoint should work."""
        resp = client.get("/metrics")
        assert resp.status_code in (200, 501)
        if resp.status_code == 200:
            assert "nebula_" in resp.text


# ============================================
# E2E Test: Vector Search
# ============================================

class TestVectorSearch:
    """Vector/semantic search workflow."""
    
    def test_vector_search(self, client: httpx.Client, auth_headers: dict):
        """Vector search should accept queries."""
        resp = client.post(
            "/api/v1/vector/search",
            headers=auth_headers,
            json={"query": "machine learning", "top_k": 5},
        )
        assert resp.status_code == 200, f"Vector search failed: {resp.text}"
        data = resp.json()
        assert "results" in data or "data" in data


# ============================================
# E2E Test: Recommendations
# ============================================

class TestRecommendations:
    """Recommendations workflow."""
    
    def test_get_recommendations(self, client: httpx.Client, auth_headers: dict):
        """Recommendations should return results."""
        resp = client.get("/api/v1/recommendations/", headers=auth_headers)
        assert resp.status_code == 200, f"Recommendations failed: {resp.text}"
        data = resp.json()
        assert "recommendations" in data or "data" in data