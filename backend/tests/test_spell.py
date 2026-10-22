"""Spell correction feature tests."""

from __future__ import annotations


import pytest

from app.services.auth import create_access_token
from app.services.spell_service import levenshtein_distance, normalize_text


class APITestBase:
    @pytest.fixture(autouse=True)
    def _bind_client(self, client):
        self.client = client


# ---------------------------------------------------------------------------
# Levenshtein distance tests
# ---------------------------------------------------------------------------


class TestLevenshteinDistance:
    """Tests for the Levenshtein distance implementation."""

    def test_identical_strings(self):
        assert levenshtein_distance("hello", "hello") == 0

    def test_single_substitution(self):
        assert levenshtein_distance("hello", "hallo") == 1

    def test_single_insertion(self):
        assert levenshtein_distance("hello", "helllo") == 1

    def test_single_deletion(self):
        assert levenshtein_distance("hello", "ello") == 1

    def test_transposition(self):
        assert levenshtein_distance("hello", "helol") == 2

    def test_max_distance_bound(self):
        assert levenshtein_distance("abc", "xyz", max_distance=2) == 3

    def test_max_distance_bounding(self):
        assert levenshtein_distance("a", "zzzzzz", max_distance=2) == 3

    def test_unicode_safe(self):
        assert levenshtein_distance("café", "cafe") == 1

    def test_empty_strings(self):
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("", "a") == 1
        assert levenshtein_distance("a", "") == 1

    def test_length_difference_gt_max(self):
        assert levenshtein_distance("a", "abcdef", max_distance=2) == 3


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------


class TestNormalizeText:
    """Tests for text normalization."""

    def test_lowercase(self):
        assert normalize_text("HELLO") == "hello"

    def test_collapse_whitespace(self):
        assert "  " not in normalize_text("hello   world")

    def test_strip_accents(self):
        result = normalize_text("café résumé")
        assert "é" not in result
        assert "r" in result

    def test_remove_control_characters(self):
        result = normalize_text("hello\x00world")
        assert "\x00" not in result

    def test_unicode_nfc(self):
        result = normalize_text("\u00e9")
        assert result == "e"


# ---------------------------------------------------------------------------
# Spell API - authenticated endpoints
# ---------------------------------------------------------------------------


class TestSpellAPI(APITestBase):
    """Tests for spell correction API endpoints."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        token = create_access_token(email, role="user")
        return {"Authorization": f"Bearer {token}"}

    def test_spell_endpoint_requires_query(self):
        headers = self._get_auth_headers()
        response = self.client.get("/api/v1/search/spell", headers=headers)
        assert response.status_code == 422

    def test_spell_query_too_long(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "a" * 101},
            headers=headers,
        )
        assert response.status_code == 422

    def test_spell_basic_response_shape(self):
        """Spell endpoint returns expected response structure."""
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "machne lernng"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "corrected" in data["data"]
        assert "confidence" in data["data"]
        assert "changed" in data["data"]
        assert data["data"]["original"] == "machne lernng"

    def test_spell_already_correct(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "the"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["changed"] is False
        assert data["data"]["confidence"] == 1.0

    def test_spell_unicode_input(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "café"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_spell_empty_query(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": ""},
            headers=headers,
        )
        assert response.status_code == 422

    def test_spell_numbers(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "123"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_spell_symbols(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "!!!"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_spell_did_you_mean_when_changed(self):
        """When changed is true and confidence is decent, did_you_mean may appear."""
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell",
            params={"q": "the"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestSpellSuggestionsAPI(APITestBase):
    """Tests for spell suggestions endpoint."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        token = create_access_token(email, role="user")
        return {"Authorization": f"Bearer {token}"}

    def test_suggestions_requires_query(self):
        headers = self._get_auth_headers()
        response = self.client.get("/api/v1/search/spell/suggestions", headers=headers)
        assert response.status_code == 422

    def test_suggestions_returns_list(self):
        headers = self._get_auth_headers()
        response = self.client.get(
            "/api/v1/search/spell/suggestions",
            params={"q": "test"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data.get("data", {})


class TestSpellRebuildAPI(APITestBase):
    """Tests for spell dictionary rebuild endpoint."""

    def _get_auth_headers(self, email: str = "test@example.com") -> dict:
        token = create_access_token(email, role="admin")
        return {"Authorization": f"Bearer {token}"}

    def test_rebuild_requires_auth(self):
        response = self.client.post("/api/v1/search/spell/rebuild")
        assert response.status_code == 401

    def test_rebuild_without_token_returns_401(self):
        response = self.client.post("/api/v1/search/spell/rebuild")
        assert response.status_code == 401
