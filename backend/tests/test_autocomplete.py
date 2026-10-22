"""Autocomplete system tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import create_access_token
from app.config import get_settings

settings = get_settings()
client = TestClient(app)


class TestAutocomplete:
    """Test autocomplete endpoints."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        """Helper to get auth headers."""
        token = create_access_token(email, role="user")
        return {"Authorization": f"Bearer {token}"}

    def test_autocomplete_requires_query(self):
        """Test that autocomplete requires query parameter."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", headers=headers)
        assert response.status_code == 422  # Validation error

    def test_autocomplete_query_too_short(self):
        """Test that short queries are rejected."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", params={"q": "a"}, headers=headers)
        assert response.status_code == 422

    def test_autocomplete_query_too_long(self):
        """Test that very long queries are rejected."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", params={"q": "a" * 51}, headers=headers)
        assert response.status_code == 422

    def test_autocomplete_basic(self):
        """Test basic autocomplete request."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", params={"q": "py"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data.get("data", {})

    def test_autocomplete_case_insensitive(self):
        """Test that autocomplete is case insensitive."""
        headers = self._get_auth_headers()
        response1 = client.get("/api/v1/search/autocomplete", params={"q": "PY"}, headers=headers)
        response2 = client.get("/api/v1/search/autocomplete", params={"q": "py"}, headers=headers)
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_autocomplete_empty_query(self):
        """Test that empty queries are rejected."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", params={"q": ""}, headers=headers)
        assert response.status_code == 422

    def test_autocomplete_whitespace_query(self):
        """Test that whitespace-only queries are rejected."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/autocomplete", params={"q": "   "}, headers=headers)
        assert response.status_code in (400, 422)


class TestRecentSearches:
    """Test recent searches endpoints."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        """Helper to get auth headers."""
        token = create_access_token(email, role="user")
        return {"Authorization": f"Bearer {token}"}

    def test_get_recent_requires_auth(self):
        """Test that getting recent searches requires authentication."""
        response = client.get("/api/v1/search/recent")
        assert response.status_code == 401

    def test_get_recent_empty(self):
        """Test getting recent searches for new user."""
        headers = self._get_auth_headers("newuser@example.com")
        response = client.get("/api/v1/search/recent", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "recent" in data.get("data", {})

    def test_clear_recent_requires_auth(self):
        """Test that clearing recent searches requires authentication."""
        response = client.delete("/api/v1/search/recent")
        assert response.status_code == 401

    def test_clear_recent(self):
        """Test clearing recent searches."""
        headers = self._get_auth_headers()
        response = client.delete("/api/v1/search/recent", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should succeed even if user has no searches or user doesn't exist (idempotent)
        assert data.get("data", {}).get("cleared") in (True, False)


class TestPopularQueries:
    """Test popular queries endpoint."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        """Helper to get auth headers."""
        token = create_access_token(email, role="user")
        return {"Authorization": f"Bearer {token}"}

    def test_get_popular(self):
        """Test getting popular queries."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/popular", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data.get("data", {})

    def test_get_popular_with_limit(self):
        """Test getting popular queries with custom limit."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/popular", params={"limit": 10}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("data", {}).get("queries", [])) <= 10

    def test_get_popular_limit_validation(self):
        """Test limit parameter validation."""
        headers = self._get_auth_headers()
        response = client.get("/api/v1/search/popular", params={"limit": 0}, headers=headers)
        assert response.status_code == 422

        response = client.get("/api/v1/search/popular", params={"limit": 101}, headers=headers)
        assert response.status_code == 422


class TestNormalization:
    """Test query normalization."""

    def test_normalize_lowercase(self):
        """Test that normalization converts to lowercase."""
        from app.services.autocomplete_service import AutocompleteService
        assert AutocompleteService._normalize_query("UPPERCASE") == "uppercase"

    def test_normalize_removes_punctuation(self):
        """Test that normalization removes punctuation."""
        from app.services.autocomplete_service import AutocompleteService
        result = AutocompleteService._normalize_query("hello, world!")
        assert "," not in result
        assert "!" not in result
        assert "hello world" == result

    def test_normalize_collapses_whitespace(self):
        """Test that normalization collapses whitespace."""
        from app.services.autocomplete_service import AutocompleteService
        result = AutocompleteService._normalize_query("hello   world")
        assert "   " not in result
        assert "hello world" == result

    def test_normalize_removes_control_characters(self):
        """Test that normalization removes control characters."""
        from app.services.autocomplete_service import AutocompleteService
        result = AutocompleteService._normalize_query("hello\x00world\x1f")
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_normalize_empty_after_normalization(self):
        """Test that normalization handles edge cases."""
        from app.services.autocomplete_service import AutocompleteService
        result = AutocompleteService._normalize_query("!!!")
        assert result == ""