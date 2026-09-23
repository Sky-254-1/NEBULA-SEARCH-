"""Tests for application configuration (app/config.py)."""

import os
import pytest
from unittest.mock import patch

from app.config import Settings, get_settings


class TestSettings:
    """Test Settings dataclass."""

    def test_default_database_url(self):
        s = Settings()
        assert s.database_url is not None
        assert isinstance(s.database_url, str)

    def test_jwt_algorithm_default(self):
        s = Settings()
        assert s.jwt_algorithm == "HS256"

    def test_jwt_expiry_minutes_default(self):
        s = Settings()
        assert s.jwt_expiry_minutes == 30

    def test_uses_postgres_false_for_sqlite(self):
        with patch.dict(os.environ, {"DATABASE_URL": "test.db"}):
            s = Settings()
            assert s.uses_postgres is False

    def test_uses_postgres_true_for_postgresql(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@host/db"}):
            s = Settings()
            assert s.uses_postgres is True

    def test_is_production_false(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            s = Settings()
            assert s.is_production is False

    def test_is_production_true(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": "a" * 32}):
            s = Settings()
            assert s.is_production is True

    def test_storage_paths_are_path_objects(self):
        s = Settings()
        from pathlib import Path
        assert isinstance(s.storage_uploads, Path)
        assert isinstance(s.storage_cache, Path)
        assert isinstance(s.storage_vector, Path)
        assert isinstance(s.storage_indexes, Path)
        assert isinstance(s.storage_exports, Path)

    def test_cors_origin_list_parses_correctly(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,http://localhost:5173"}):
            s = Settings()
            origins = s.cors_origin_list
            assert "http://localhost:3000" in origins
            assert "http://localhost:5173" in origins

    def test_cors_wildcard_raises(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            s = Settings()
            with pytest.raises(ValueError, match="CORS_ORIGINS"):
                _ = s.cors_origin_list

    def test_csp_policy_includes_directives(self):
        s = Settings()
        policy = s.csp_policy
        assert "default-src" in policy
        assert "script-src" in policy
        assert "style-src" in policy

    def test_encryption_key_bytes_length(self):
        s = Settings()
        key = s.encryption_key_bytes
        assert len(key) == 32

    def test_rate_limit_defaults(self):
        s = Settings()
        assert s.rate_limit_per_minute == 1000
        assert s.max_login_attempts == 5

    def test_jwt_issuer_audience_defaults(self):
        s = Settings()
        assert s.jwt_issuer == "Nebula Search"
        assert s.jwt_audience == "nebula-search-api"

    def test_cookie_defaults(self):
        s = Settings()
        assert s.cookie_samesite in ("lax", "strict", "none")

    def test_ai_provider_default(self):
        s = Settings()
        assert s.ai_provider in ("auto", "openai", "ollama", "gguf")

    def test_indexing_settings(self):
        s = Settings()
        assert s.indexing_chunk_size > 0
        assert s.indexing_chunk_overlap >= 0
        assert s.indexing_worker_count >= 1

    def test_get_settings_is_cached(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_refresh_token_days_default(self):
        s = Settings()
        assert s.refresh_token_days == 30

    def test_email_verification_expiry(self):
        s = Settings()
        assert s.email_verification_expiry_hours > 0
        assert s.password_reset_expiry_hours > 0

    def test_log_level_default(self):
        s = Settings()
        assert s.log_level.upper() in ("DEBUG", "INFO", "WARNING", "ERROR")

    def test_totp_issuer_default(self):
        s = Settings()
        assert s.totp_issuer == "Nebula Search"

    def test_crawler_settings(self):
        s = Settings()
        assert s.crawler_max_concurrency > 0
        assert s.crawler_max_depth > 0
        assert s.crawler_default_delay >= 0
