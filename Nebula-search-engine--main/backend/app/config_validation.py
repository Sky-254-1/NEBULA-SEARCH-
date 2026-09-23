"""
Configuration validation for Nebula Search.
Validates all required settings at startup to prevent runtime failures.
"""

import logging
import os
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """Validates application configuration at startup."""

    def __init__(self, settings):
        self.settings = settings
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> ConfigValidationResult:
        """Run all validations and return result."""
        self.validate_environment()
        self.validate_security()
        self.validate_database()
        self.validate_redis()
        self.validate_storage()
        self.validate_external_services()
        self.validate_performance()

        return ConfigValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
        )

    def validate_environment(self):
        """Validate environment configuration."""
        # Check if environment is set
        if not self.settings.app_env:
            self.errors.append("APP_ENV is not set")

        # Validate environment value
        try:
            env = Environment(self.settings.app_env)
        except ValueError:
            self.errors.append(f"Invalid APP_ENV: {self.settings.app_env}")

        # Production checks
        if self.settings.is_production:
            if self.settings.log_level.upper() == "DEBUG":
                self.warnings.append("Log level is DEBUG in production (recommended: INFO or WARNING)")

    def validate_security(self):
        """Validate security settings."""
        # JWT Secret
        if not self.settings.jwt_secret:
            self.errors.append("JWT_SECRET is required")
        elif len(self.settings.jwt_secret) < 32:
            self.errors.append("JWT_SECRET must be at least 32 characters")
        elif self.settings.is_production and self.settings.jwt_secret in ["change-me", "secret", "your-secret-key"]:
            self.errors.append("JWT_SECRET must be changed from default value in production")

        # CORS origins in production
        if self.settings.is_production:
            cors_origins = self.settings.cors_origin_list
            if not cors_origins or cors_origins == ["*"]:
                self.errors.append("CORS_ORIGINS must be restricted in production (not '*')")
            elif "localhost" in str(cors_origins) or "127.0.0.1" in str(cors_origins):
                self.warnings.append("CORS_ORIGINS contains localhost in production")

        # Encryption key
        if hasattr(self.settings, 'encryption_key') and not self.settings.encryption_key:
            self.warnings.append("ENCRYPTION_KEY is not set (encrypted features will be disabled)")

    def validate_database(self):
        """Validate database configuration."""
        if not self.settings.database_url:
            self.errors.append("DATABASE_URL is required")
        else:
            # Check if PostgreSQL is configured
            if not self.settings.database_url.startswith(("postgresql://", "postgres://")):
                if self.settings.is_production:
                    self.warnings.append("SQLite detected in production (PostgreSQL recommended)")

            # Validate connection pool settings
            if hasattr(self.settings, 'db_pool_size') and self.settings.db_pool_size < 5:
                self.warnings.append(f"DB_POOL_SIZE is very low: {self.settings.db_pool_size}")

    def validate_redis(self):
        """Validate Redis configuration."""
        if hasattr(self.settings, 'redis_url') and self.settings.redis_url:
            # Redis is configured
            if self.settings.is_production and "localhost" in self.settings.redis_url:
                self.warnings.append("Redis URL points to localhost in production")

    def validate_storage(self):
        """Validate storage configuration."""
        # Check storage backend
        if hasattr(self.settings, 'storage_backend'):
            valid_backends = ["local", "s3", "minio"]
            if self.settings.storage_backend not in valid_backends:
                self.errors.append(f"Invalid STORAGE_BACKEND: {self.settings.storage_backend}")

            # S3 checks
            if self.settings.storage_backend == "s3":
                if not hasattr(self.settings, 'aws_access_key_id') or not self.settings.aws_access_key_id:
                    self.errors.append("AWS_ACCESS_KEY_ID is required for S3 storage")
                if not hasattr(self.settings, 'aws_secret_access_key') or not self.settings.aws_secret_access_key:
                    self.errors.append("AWS_SECRET_ACCESS_KEY is required for S3 storage")
                if not hasattr(self.settings, 's3_bucket') or not self.settings.s3_bucket:
                    self.errors.append("S3_BUCKET is required for S3 storage")

        # Check storage directories exist
        storage_dirs = [
            self.settings.storage_uploads,
            self.settings.storage_cache,
            self.settings.storage_vector,
            self.settings.storage_indexes,
        ]
        for path in storage_dirs:
            if not os.path.exists(path):
                self.warnings.append(f"Storage directory does not exist: {path}")

    def validate_external_services(self):
        """Validate external service configuration."""
        # Elasticsearch is optional but warn if URL is set but service might not be reachable
        if hasattr(self.settings, 'elasticsearch_url') and self.settings.elasticsearch_url:
            if "localhost" in self.settings.elasticsearch_url or "127.0.0.1" in self.settings.elasticsearch_url:
                self.warnings.append("Elasticsearch URL points to localhost - ensure service is running")

        # OpenAI API key
        if hasattr(self.settings, 'openai_api_key') and not self.settings.openai_api_key:
            self.warnings.append("OPENAI_API_KEY is not set (AI features will be limited)")

        # Email configuration
        if self.settings.smtp_host:
            if not self.settings.smtp_username:
                self.warnings.append("SMTP_USERNAME is not set (authentication may fail)")

    def validate_performance(self):
        """Validate performance settings."""
        # Worker count
        if hasattr(self.settings, 'max_workers'):
            if self.settings.max_workers < 1:
                self.errors.append("MAX_WORKERS must be at least 1")
            elif self.settings.max_workers > 16:
                self.warnings.append(f"MAX_WORKERS is very high: {self.settings.max_workers} (recommended: 2-8)")

        # Rate limiting
        if hasattr(self.settings, 'rate_limit_requests'):
            if self.settings.rate_limit_requests < 10:
                self.warnings.append(f"RATE_LIMIT_REQUESTS is very low: {self.settings.rate_limit_requests}")

        # Session timeout
        if hasattr(self.settings, 'session_timeout'):
            if self.settings.session_timeout < 300:
                self.warnings.append(f"SESSION_TIMEOUT is very low: {self.settings.session_timeout}s (recommended: 3600s)")

    def generate_recommendations(self) -> list[str]:
        """Generate configuration recommendations."""
        recommendations = []

        if self.settings.is_production:
            # Production recommendations
            if not hasattr(self.settings, 'sentry_dsn') or not self.settings.sentry_dsn:
                recommendations.append("Set SENTRY_DSN for error tracking")

            if not hasattr(self.settings, 'otel_exporter_otlp_endpoint') or not self.settings.otel_exporter_otlp_endpoint:
                recommendations.append("Set OTEL_EXPORTER_OTLP_ENDPOINT for distributed tracing")

            if not hasattr(self.settings, 'redis_url') or not self.settings.redis_url:
                recommendations.append("Configure Redis for caching and session storage")

            if not hasattr(self.settings, 'elasticsearch_url') or not self.settings.elasticsearch_url:
                recommendations.append("Configure Elasticsearch for vector search capabilities")

        return recommendations


def validate_config(settings) -> ConfigValidationResult:
    """
    Validate application configuration.
    Returns validation result with errors and warnings.
    """
    validator = ConfigValidator(settings)
    result = validator.validate_all()

    # Log results
    if result.errors:
        for error in result.errors:
            logger.error("Configuration error: %s", error)

    if result.warnings:
        for warning in result.warnings:
            logger.warning("Configuration warning: %s", warning)

    recommendations = validator.generate_recommendations()
    for rec in recommendations:
        logger.info("Configuration recommendation: %s", rec)

    return result


def generate_secure_secret(length: int = 32) -> str:
    """Generate a cryptographically secure random secret."""
    return secrets.token_urlsafe(length)


def validate_jwt_secret(secret: Optional[str], is_production: bool = False) -> tuple[bool, str]:
    """
    Validate JWT secret strength.
    Returns (is_valid, message).
    """
    if not secret:
        return False, "JWT_SECRET is not set"

    if len(secret) < 32:
        return False, f"JWT_SECRET is too short ({len(secret)} chars, minimum 32)"

    if is_production:
        weak_secrets = ["change-me", "secret", "your-secret-key", "changeme", "password"]
        if secret.lower() in weak_secrets:
            return False, "JWT_SECRET uses a common weak value"

        # Check for sufficient entropy
        unique_chars = len(set(secret))
        if unique_chars < 16:
            return False, f"JWT_SECRET has low entropy ({unique_chars} unique characters, minimum 16)"

    return True, "JWT_SECRET is valid"