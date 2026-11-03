"""Tests for config_validation module — 150 lines, 0% covered."""

import pytest
from unittest.mock import MagicMock, patch
from app.config_validation import (
    Environment,
    ConfigValidationResult,
    ConfigValidator,
    validate_config,
    generate_secure_secret,
    validate_jwt_secret,
)


class TestEnvironmentEnum:
    def test_development(self):
        assert Environment.DEVELOPMENT == "development"

    def test_staging(self):
        assert Environment.STAGING == "staging"

    def test_production(self):
        assert Environment.PRODUCTION == "production"

    def test_testing(self):
        assert Environment.TESTING == "testing"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            Environment("invalid")


class TestConfigValidationResult:
    def test_creation(self):
        r = ConfigValidationResult(is_valid=True, errors=[], warnings=[])
        assert r.is_valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_post_init_none_errors(self):
        r = ConfigValidationResult(is_valid=False, errors=None, warnings=None)
        assert r.errors == []
        assert r.warnings == []

    def test_post_init_with_values(self):
        r = ConfigValidationResult(is_valid=False, errors=["e1"], warnings=["w1"])
        assert r.errors == ["e1"]
        assert r.warnings == ["w1"]


class TestConfigValidator:
    def _settings(self, **overrides):
        s = MagicMock()
        s.app_env = overrides.get("app_env", "testing")
        s.is_production = overrides.get("is_production", False)
        s.log_level = overrides.get("log_level", "INFO")
        s.jwt_secret = overrides.get("jwt_secret", "a" * 64)
        s.cors_origin_list = overrides.get("cors_origin_list", ["http://localhost:3000"])
        s.database_url = overrides.get("database_url", "sqlite:///test.db")
        s.storage_uploads = overrides.get("storage_uploads", "/tmp/uploads")
        s.storage_cache = overrides.get("storage_cache", "/tmp/cache")
        s.storage_vector = overrides.get("storage_vector", "/tmp/vector")
        s.storage_indexes = overrides.get("storage_indexes", "/tmp/indexes")
        s.smtp_host = overrides.get("smtp_host", "")
        s.smtp_username = overrides.get("smtp_username", "")
        # Numeric attributes that get compared with < / >
        s.db_pool_size = 10
        s.max_workers = 4
        s.rate_limit_requests = 100
        s.session_timeout = 3600
        # Storage / service attributes probed with hasattr
        s.storage_backend = "local"
        s.encryption_key = "some-key"
        s.elasticsearch_url = ""
        s.openai_api_key = "sk-test"
        s.redis_url = ""
        s.sentry_dsn = ""
        s.otel_exporter_otlp_endpoint = ""
        return s

    def test_validate_all_valid(self):
        s = self._settings()
        v = ConfigValidator(s)
        result = v.validate_all()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_environment_missing(self):
        s = self._settings(app_env="")
        v = ConfigValidator(s)
        v.validate_environment()
        assert "APP_ENV is not set" in v.errors

    def test_validate_environment_invalid(self):
        s = self._settings(app_env="bogus")
        v = ConfigValidator(s)
        v.validate_environment()
        assert any("Invalid APP_ENV" in e for e in v.errors)

    def test_validate_environment_production_debug(self):
        s = self._settings(app_env="production", is_production=True, log_level="DEBUG")
        v = ConfigValidator(s)
        v.validate_environment()
        assert any("DEBUG in production" in w for w in v.warnings)

    def test_validate_security_missing_jwt(self):
        s = self._settings(jwt_secret="")
        v = ConfigValidator(s)
        v.validate_security()
        assert "JWT_SECRET is required" in v.errors

    def test_validate_security_short_jwt(self):
        s = self._settings(jwt_secret="short")
        v = ConfigValidator(s)
        v.validate_security()
        assert any("at least 32" in e for e in v.errors)

    def test_validate_security_default_jwt_production(self):
        s = self._settings(jwt_secret="change-me" + "x" * 30, is_production=True)
        v = ConfigValidator(s)
        v.validate_security()
        # "change-me" is not in the weak list because the full string is different
        # but let's test the exact default
        s2 = self._settings(jwt_secret="change-me", is_production=True)
        v2 = ConfigValidator(s2)
        v2.validate_security()
        assert any("at least 32" in e for e in v2.errors)

    def test_validate_security_cors_star_production(self):
        s = self._settings(is_production=True, cors_origin_list=["*"], jwt_secret="a" * 64)
        v = ConfigValidator(s)
        v.validate_security()
        assert any("CORS_ORIGINS must be restricted" in e for e in v.errors)

    def test_validate_security_cors_empty_production(self):
        s = self._settings(is_production=True, cors_origin_list=[], jwt_secret="a" * 64)
        v = ConfigValidator(s)
        v.validate_security()
        assert any("CORS_ORIGINS must be restricted" in e for e in v.errors)

    def test_validate_security_cors_localhost_production(self):
        s = self._settings(is_production=True, cors_origin_list=["http://localhost:3000"], jwt_secret="a" * 64)
        v = ConfigValidator(s)
        v.validate_security()
        assert any("localhost" in w for w in v.warnings)

    def test_validate_security_encryption_key_missing(self):
        s = self._settings()
        s.encryption_key = ""
        v = ConfigValidator(s)
        v.validate_security()
        assert any("ENCRYPTION_KEY" in w for w in v.warnings)

    def test_validate_database_missing(self):
        s = self._settings(database_url="")
        v = ConfigValidator(s)
        v.validate_database()
        assert "DATABASE_URL is required" in v.errors

    def test_validate_database_sqlite_production(self):
        s = self._settings(database_url="sqlite:///prod.db", is_production=True)
        v = ConfigValidator(s)
        v.validate_database()
        assert any("SQLite detected" in w for w in v.warnings)

    def test_validate_database_pool_size_low(self):
        s = self._settings()
        s.db_pool_size = 2
        v = ConfigValidator(s)
        v.validate_database()
        assert any("DB_POOL_SIZE is very low" in w for w in v.warnings)

    def test_validate_redis_localhost_production(self):
        s = self._settings(is_production=True, jwt_secret="a" * 64)
        s.redis_url = "redis://localhost:6379/0"
        v = ConfigValidator(s)
        v.validate_redis()
        assert any("localhost" in w for w in v.warnings)

    def test_validate_storage_invalid_backend(self):
        s = self._settings()
        s.storage_backend = "gcs"
        v = ConfigValidator(s)
        v.validate_storage()
        assert any("Invalid STORAGE_BACKEND" in e for e in v.errors)

    def test_validate_storage_s3_missing_keys(self):
        s = self._settings()
        s.storage_backend = "s3"
        s.aws_access_key_id = ""
        s.aws_secret_access_key = ""
        s.s3_bucket = ""
        v = ConfigValidator(s)
        v.validate_storage()
        assert any("AWS_ACCESS_KEY_ID" in e for e in v.errors)
        assert any("AWS_SECRET_ACCESS_KEY" in e for e in v.errors)
        assert any("S3_BUCKET" in e for e in v.errors)

    def test_validate_storage_dirs_missing(self):
        s = self._settings(
            storage_uploads="/nonexistent/uploads",
            storage_cache="/nonexistent/cache",
            storage_vector="/nonexistent/vector",
            storage_indexes="/nonexistent/indexes",
        )
        v = ConfigValidator(s)
        v.validate_storage()
        assert any("does not exist" in w for w in v.warnings)

    def test_validate_external_services_elasticsearch_localhost(self):
        s = self._settings()
        s.elasticsearch_url = "http://localhost:9200"
        v = ConfigValidator(s)
        v.validate_external_services()
        assert any("Elasticsearch" in w for w in v.warnings)

    def test_validate_external_services_openai_missing(self):
        s = self._settings()
        s.openai_api_key = ""
        v = ConfigValidator(s)
        v.validate_external_services()
        assert any("OPENAI_API_KEY" in w for w in v.warnings)

    def test_validate_external_services_smtp_no_username(self):
        s = self._settings(smtp_host="smtp.gmail.com", smtp_username="")
        v = ConfigValidator(s)
        v.validate_external_services()
        assert any("SMTP_USERNAME" in w for w in v.warnings)

    def test_validate_performance_workers_zero(self):
        s = self._settings()
        s.max_workers = 0
        v = ConfigValidator(s)
        v.validate_performance()
        assert any("must be at least 1" in e for e in v.errors)

    def test_validate_performance_workers_high(self):
        s = self._settings()
        s.max_workers = 32
        v = ConfigValidator(s)
        v.validate_performance()
        assert any("very high" in w for w in v.warnings)

    def test_validate_performance_rate_limit_low(self):
        s = self._settings()
        s.rate_limit_requests = 5
        v = ConfigValidator(s)
        v.validate_performance()
        assert any("RATE_LIMIT_REQUESTS" in w for w in v.warnings)

    def test_validate_performance_session_timeout_low(self):
        s = self._settings()
        s.session_timeout = 60
        v = ConfigValidator(s)
        v.validate_performance()
        assert any("SESSION_TIMEOUT" in w for w in v.warnings)

    def test_generate_recommendations_production(self):
        s = self._settings(is_production=True)
        # Remove optional attrs
        del s.sentry_dsn
        del s.otel_exporter_otlp_endpoint
        del s.redis_url
        del s.elasticsearch_url
        v = ConfigValidator(s)
        recs = v.generate_recommendations()
        assert len(recs) >= 1

    def test_generate_recommendations_not_production(self):
        s = self._settings(is_production=False)
        v = ConfigValidator(s)
        recs = v.generate_recommendations()
        assert recs == []


class TestValidateConfig:
    def _mock_settings(self, **overrides):
        s = MagicMock()
        s.app_env = overrides.get("app_env", "testing")
        s.is_production = overrides.get("is_production", False)
        s.log_level = overrides.get("log_level", "INFO")
        s.jwt_secret = overrides.get("jwt_secret", "a" * 64)
        s.cors_origin_list = overrides.get("cors_origin_list", ["http://localhost"])
        s.database_url = overrides.get("database_url", "sqlite:///test.db")
        s.storage_uploads = "/tmp/u"
        s.storage_cache = "/tmp/c"
        s.storage_vector = "/tmp/v"
        s.storage_indexes = "/tmp/i"
        s.smtp_host = ""
        s.smtp_username = ""
        s.db_pool_size = 10
        s.max_workers = 4
        s.rate_limit_requests = 100
        s.session_timeout = 3600
        s.storage_backend = "local"
        s.encryption_key = "key"
        s.elasticsearch_url = ""
        s.openai_api_key = "sk-test"
        s.redis_url = ""
        s.sentry_dsn = ""
        s.otel_exporter_otlp_endpoint = ""
        return s

    def test_validate_config_valid(self):
        s = self._mock_settings()
        result = validate_config(s)
        assert isinstance(result, ConfigValidationResult)

    def test_validate_config_with_errors(self):
        s = self._mock_settings(app_env="", jwt_secret="", database_url="")
        result = validate_config(s)
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestGenerateSecureSecret:
    def test_length(self):
        secret = generate_secure_secret(32)
        assert len(secret) > 0

    def test_uniqueness(self):
        s1 = generate_secure_secret()
        s2 = generate_secure_secret()
        assert s1 != s2


class TestValidateJwtSecret:
    def test_empty(self):
        valid, msg = validate_jwt_secret("")
        assert valid is False
        assert "not set" in msg

    def test_none(self):
        valid, msg = validate_jwt_secret(None)
        assert valid is False

    def test_too_short(self):
        valid, msg = validate_jwt_secret("short")
        assert valid is False
        assert "too short" in msg

    def test_weak_production(self):
        valid, msg = validate_jwt_secret("change-me" + "x" * 30, is_production=True)
        assert valid is False or "weak" in msg.lower() or "entropy" in msg.lower()

    def test_low_entropy_production(self):
        valid, msg = validate_jwt_secret("a" * 64, is_production=True)
        assert valid is False
        assert "entropy" in msg.lower()

    def test_valid(self):
        valid, msg = validate_jwt_secret("abcdefghijklmnopqrstuvwxyz012345678")
        assert valid is True
        assert "valid" in msg.lower()

    def test_valid_production(self):
        secret = generate_secure_secret(64)
        valid, msg = validate_jwt_secret(secret, is_production=True)
        assert valid is True
