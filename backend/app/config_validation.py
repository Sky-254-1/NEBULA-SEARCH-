"""Startup configuration validation.

Validates required environment variables before application startup.
Raises clear errors with variable names (never values) if required
variables are missing or invalid.
"""

import os
import sys
from typing import List, Optional, Dict, Tuple


class ValidationError(Exception):
    """Raised when environment validation fails."""
    pass


def get_env_or_none(key: str) -> Optional[str]:
    """Get environment variable or None if not set."""
    return os.getenv(key)


def get_env_value(key: str) -> str:
    """Get environment variable or empty string if not set."""
    value = os.getenv(key)
    return value if value is not None else ""


def validate_required_variables(required: List[str], app_env: str) -> List[str]:
    """Validate that all required environment variables are set.
    
    Args:
        required: List of required environment variable names
        app_env: Current application environment (development/production)
    
    Returns:
        List of missing variable names
    
    Raises:
        ValidationError: If any required variable is missing in production
    """
    missing = []
    
    for var in required:
        value = get_env_or_none(var)
        if value is None or value == "":
            missing.append(var)
    
    if missing:
        if app_env == "production":
            # In production, missing required variables are fatal
            raise ValidationError(
                f"Missing required environment variables in {app_env} mode: "
                f"{', '.join(sorted(missing))}. "
                "These must be set before starting the application."
            )
        else:
            # In development, return missing variables for warning
            return missing
    
    return []


def validate_min_length(var_name: str, value: str, min_length: int, app_env: str) -> bool:
    """Validate that a value meets minimum length requirements.
    
    Args:
        var_name: Environment variable name (for error messages)
        value: The value to validate
        min_length: Minimum required length
        app_env: Current application environment
    
    Returns:
        True if validation failed (for tracking), False if passed
    """
    if len(value) < min_length:
        if app_env == "production":
            raise ValidationError(
                f"{var_name} must be at least {min_length} characters in production. "
                f"Current length: {len(value)}. "
                f"Generate a secure secret with: python -c 'import secrets; print(secrets.token_hex({min_length // 2}))'"
            )
        return True
    return False


def validate_not_placeholder(var_name: str, value: str, app_env: str) -> bool:
    """Check if value is a placeholder that shouldn't be in production.
    
    Args:
        var_name: Environment variable name
        value: The value to check
        app_env: Current application environment
    
    Returns:
        True if placeholder detected (for tracking), False otherwise
    """
    placeholders = [
        "change-me", "your-", "-here", "placeholder", "example",
        "sample", "dummy", "default-value"
    ]
    
    is_placeholder = any(p in value.lower() for p in placeholders)
    
    if is_placeholder and app_env == "production":
        raise ValidationError(
            f"{var_name} appears to be using a placeholder value in production. "
            "Replace with a secure, randomly generated value."
        )
    
    return is_placeholder


def validate_jwt_secret(value: str, app_env: str) -> None:
    """Validate JWT_SECRET meets minimum requirements.
    
    Args:
        value: The JWT_SECRET value
        app_env: Current application environment
    
    Raises:
        ValidationError: If JWT_SECRET is invalid
    """
    var_name = "JWT_SECRET"
    
    # Check if set
    if value == "":
        if app_env == "production":
            raise ValidationError(
                f"{var_name} must be set in production. "
                "Generate a secure secret with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        return
    
    # Check length in production
    validate_min_length(var_name, value, 32, app_env)
    
    # Check for placeholder in production
    validate_not_placeholder(var_name, value, app_env)


def validate_session_secret(value: str, app_env: str) -> None:
    """Validate SESSION_SECRET meets minimum requirements.
    
    Args:
        value: The SESSION_SECRET value
        app_env: Current application environment
    
    Raises:
        ValidationError: If SESSION_SECRET is invalid
    """
    var_name = "SESSION_SECRET"
    
    # Check if set
    if value == "":
        if app_env == "production":
            raise ValidationError(
                f"{var_name} must be set in production. "
                "Generate a secure secret with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return
    
    # Check length in production
    validate_min_length(var_name, value, 32, app_env)
    
    # Check for placeholder in production
    validate_not_placeholder(var_name, value, app_env)


def validate_encryption_key(value: str, app_env: str) -> None:
    """Validate ENCRYPTION_KEY meets minimum requirements.
    
    Args:
        value: The ENCRYPTION_KEY value
        app_env: Current application environment
    
    Raises:
        ValidationError: If ENCRYPTION_KEY is invalid
    """
    var_name = "ENCRYPTION_KEY"
    
    # Check if set
    if value == "":
        if app_env == "production":
            raise ValidationError(
                f"{var_name} must be set in production. "
                "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return
    
    # Check length in production (32 bytes for AES-256)
    validate_min_length(var_name, value, 32, app_env)
    
    # Check for placeholder in production
    validate_not_placeholder(var_name, value, app_env)


def validate_database_url(value: str, app_env: str) -> bool:
    """Validate DATABASE_URL format.
    
    Args:
        value: The DATABASE_URL value
        app_env: Current application environment
    
    Returns:
        True if format appears invalid (for tracking), False otherwise
    
    Raises:
        ValidationError: If DATABASE_URL is missing in production
    """
    var_name = "DATABASE_URL"
    
    # Check if set
    if value == "":
        if app_env == "production":
            raise ValidationError(
                f"{var_name} must be set in production. "
                "Format: postgresql://user:password@host:5432/database"
            )
        return False
    
    # Validate format
    valid_prefixes = ("postgresql://", "sqlite://")
    
    # Support legacy nebula.db format
    if value == "nebula.db":
        return False
    
    if not any(value.startswith(prefix) for prefix in valid_prefixes):
        print(
            f"WARNING: {var_name} may not be valid. Expected format: postgresql://user:pass@host:port/db",
            file=sys.stderr
        )
        return True
    
    return False


def validate_database_credentials(postgres_user: str, postgres_password: str, app_env: str, using_database_url: bool) -> List[str]:
    """Validate PostgreSQL credentials are set when using PostgreSQL without DATABASE_URL.
    
    Args:
        postgres_user: POSTGRES_USER value
        postgres_password: POSTGRES_PASSWORD value
        app_env: Current application environment
        using_database_url: Whether DATABASE_URL is being used (which contains credentials)
    
    Returns:
        List of missing credential variables
    """
    # If using DATABASE_URL, credentials are embedded in the URL
    if using_database_url:
        return []
    
    missing = []
    
    if postgres_user == "":
        missing.append("POSTGRES_USER")
    
    if postgres_password == "":
        missing.append("POSTGRES_PASSWORD")
    
    if missing and app_env == "production":
        raise ValidationError(
            f"PostgreSQL credentials missing in production: {', '.join(sorted(missing))}. "
            "Set these or use DATABASE_URL instead."
        )
    
    return missing


def validate_smtp_config(smtp_host: str, smtp_user: str, smtp_password: str, app_env: str) -> List[str]:
    """Validate SMTP configuration.
    
    Args:
        smtp_host: SMTP_HOST value
        smtp_user: SMTP_USERNAME value
        smtp_password: SMTP_PASSWORD value
        app_env: Current application environment
    
    Returns:
        List of missing SMTP configuration variables
    """
    missing = []
    
    if smtp_host == "":
        missing.append("SMTP_HOST")
    
    if smtp_user == "":
        missing.append("SMTP_USERNAME")
    
    if smtp_password == "":
        missing.append("SMTP_PASSWORD")
    
    if missing and app_env == "production" and smtp_host != "":
        # If SMTP_HOST is set in production, credentials should be too
        raise ValidationError(
            f"SMTP configuration incomplete in production. Missing: {', '.join(sorted(missing))}. "
            "These are required for email functionality."
        )
    
    return missing


def validate_cors_origins(value: str) -> bool:
    """Validate CORS_ORIGINS format.
    
    Args:
        value: The CORS_ORIGINS value
    
    Returns:
        True if warning issued, False otherwise
    """
    if value == "":
        print(
            "WARNING: CORS_ORIGINS is not set. Defaulting to localhost for development.",
            file=sys.stderr
        )
        return True
    
    if value.strip() == "*":
        print(
            "WARNING: CORS_ORIGINS='*' is insecure when using credentials. "
            "Set explicit origins for production.",
            file=sys.stderr
        )
        return True
    
    return False


def validate_minio_config(minio_root_user: str, minio_root_password: str, app_env: str) -> List[str]:
    """Validate MinIO configuration.
    
    Args:
        minio_root_user: MINIO_ROOT_USER value
        minio_root_password: MINIO_ROOT_PASSWORD value
        app_env: Current application environment
    
    Returns:
        List of missing MinIO credentials
    """
    missing = []
    
    if minio_root_user == "":
        missing.append("MINIO_ROOT_USER")
    
    if minio_root_password == "":
        missing.append("MINIO_ROOT_PASSWORD")
    
    if missing and app_env == "production":
        raise ValidationError(
            f"MinIO credentials missing in production: {', '.join(sorted(missing))}. "
            "These are required for object storage."
        )
    
    return missing


def validate_github_oauth(client_id: str, client_secret: str, app_env: str) -> List[str]:
    """Validate GitHub OAuth configuration.
    
    Args:
        client_id: GITHUB_OAUTH2_CLIENT_ID value
        client_secret: GITHUB_OAUTH2_CLIENT_SECRET value
        app_env: Current application environment
    
    Returns:
        List of missing OAuth credentials
    """
    missing = []
    
    if client_id == "":
        missing.append("GITHUB_OAUTH2_CLIENT_ID")
    
    if client_secret == "":
        missing.append("GITHUB_OAUTH2_CLIENT_SECRET")
    
    if missing and app_env == "production":
        raise ValidationError(
            f"GitHub OAuth credentials missing in production: {', '.join(sorted(missing))}. "
            "These are required for GitHub SSO."
        )
    
    return missing


def validate_google_oauth(client_id: str, client_secret: str, app_env: str) -> List[str]:
    """Validate Google OAuth configuration.
    
    Args:
        client_id: GOOGLE_OAUTH2_CLIENT_ID value
        client_secret: GOOGLE_OAUTH2_CLIENT_SECRET value
        app_env: Current application environment
    
    Returns:
        List of missing OAuth credentials
    """
    missing = []
    
    if client_id == "":
        missing.append("GOOGLE_OAUTH2_CLIENT_ID")
    
    if client_secret == "":
        missing.append("GOOGLE_OAUTH2_CLIENT_SECRET")
    
    if missing and app_env == "production":
        raise ValidationError(
            f"Google OAuth credentials missing in production: {', '.join(sorted(missing))}. "
            "These are required for Google SSO."
        )
    
    return missing


def validate_saml_config(enabled: str, metadata_url: str, cert_path: str, key_path: str, app_env: str) -> List[str]:
    """Validate SAML configuration when SAML is enabled.
    
    Args:
        enabled: ENABLE_SAML value
        metadata_url: SAML_METADATA_URL value
        cert_path: SAML_CERT_PATH value
        key_path: SAML_KEY_PATH value
        app_env: Current application environment
    
    Returns:
        List of missing SAML configuration variables
    """
    if enabled.lower() != "true":
        return []
    
    missing = []
    
    if metadata_url == "":
        missing.append("SAML_METADATA_URL")
    
    if cert_path == "":
        missing.append("SAML_CERT_PATH")
    
    if key_path == "":
        missing.append("SAML_KEY_PATH")
    
    if missing and app_env == "production":
        raise ValidationError(
            f"SAML configuration incomplete in production: {', '.join(sorted(missing))}. "
            "These are required for SAML SSO."
        )
    
    return missing


def validate_redis_url(value: str, app_env: str) -> bool:
    """Validate Redis URL format.
    
    Args:
        value: REDIS_URL value
        app_env: Current application environment
    
    Returns:
        True if format invalid, False otherwise
    """
    if value == "":
        if app_env == "production":
            print(
                "WARNING: REDIS_URL is not set. Redis is recommended for production caching.",
                file=sys.stderr
            )
        return False
    
    if not value.startswith("redis://") and not value.startswith("rediss://"):
        print(
            f"WARNING: REDIS_URL may not be valid. Expected redis:// or rediss://",
            file=sys.stderr
        )
        return True
    
    return False


def validate_openai_api_key(value: str, app_env: str) -> bool:
    """Validate OpenAI API key is not placeholder in production.
    
    Args:
        value: OPENAI_API_KEY value
        app_env: Current application environment
    
    Returns:
        True if placeholder detected, False otherwise
    """
    if value == "":
        return False
    
    if app_env == "production":
        if validate_not_placeholder("OPENAI_API_KEY", value, app_env):
            return True
    
    return False


def run_validations() -> bool:
    """Run all environment validations.
    
    Returns:
        True if all validations passed (or warnings only), False if invalid.
    
    Raises:
        ValidationError: If any production validation fails
    """
    app_env = get_env_or_none("APP_ENV") or "development"
    
    # Collect all warnings for development summary
    warnings = []
    
    # Define required variables based on environment
    required = ["APP_ENV"]
    
    # Always require DATABASE_URL (or legacy format)
    db_url = get_env_value("DATABASE_URL")
    if db_url == "" or db_url == "nebula.db":
        # Default SQLite is fine
        pass
    elif db_url.startswith("postgresql://"):
        required.append("DATABASE_URL")
    
    if app_env == "production":
        required.extend(["JWT_SECRET", "SESSION_SECRET", "ENCRYPTION_KEY"])
    
    # Run required variable validation
    missing = validate_required_variables(required, app_env)
    if missing:
        warnings.extend(missing)
    
    # Get all environment values
    jwt_secret = get_env_value("JWT_SECRET")
    session_secret = get_env_value("SESSION_SECRET")
    encryption_key = get_env_value("ENCRYPTION_KEY")
    cors_origins = get_env_value("CORS_ORIGINS")
    
    postgres_user = get_env_value("POSTGRES_USER")
    postgres_password = get_env_value("POSTGRES_PASSWORD")
    
    smtp_host = get_env_value("SMTP_HOST")
    smtp_user = get_env_value("SMTP_USERNAME")
    smtp_password = get_env_value("SMTP_PASSWORD")
    
    minio_user = get_env_value("MINIO_ROOT_USER")
    minio_password = get_env_value("MINIO_ROOT_PASSWORD")
    
    github_client_id = get_env_value("GITHUB_OAUTH2_CLIENT_ID")
    github_client_secret = get_env_value("GITHUB_OAUTH2_CLIENT_SECRET")
    
    google_client_id = get_env_value("GOOGLE_OAUTH2_CLIENT_ID")
    google_client_secret = get_env_value("GOOGLE_OAUTH2_CLIENT_SECRET")
    
    saml_enabled = get_env_value("ENABLE_SAML")
    saml_metadata_url = get_env_value("SAML_METADATA_URL")
    saml_cert_path = get_env_value("SAML_CERT_PATH")
    saml_key_path = get_env_value("SAML_KEY_PATH")
    
    redis_url = get_env_value("REDIS_URL")
    openai_key = get_env_value("OPENAI_API_KEY")
    
    # Run all validations and collect warnings/errors
    validation_errors = []
    
    # JWT Secret
    try:
        validate_jwt_secret(jwt_secret, app_env)
    except ValidationError as e:
        validation_errors.append(str(e))
    
    # Session Secret
    try:
        validate_session_secret(session_secret, app_env)
    except ValidationError as e:
        validation_errors.append(str(e))
    
    # Encryption Key
    try:
        validate_encryption_key(encryption_key, app_env)
    except ValidationError as e:
        validation_errors.append(str(e))
    
    # Database URL
    try:
        validate_database_url(db_url, app_env)
    except ValidationError as e:
        validation_errors.append(str(e))
    
    # PostgreSQL credentials (if using PostgreSQL without DATABASE_URL)
    using_db_url = db_url.startswith("postgresql://")
    if db_url.startswith("postgresql://"):
        try:
            validate_database_credentials(postgres_user, postgres_password, app_env, using_db_url)
        except ValidationError as e:
            validation_errors.append(str(e))
    
    # SMTP Configuration
    if smtp_host != "":
        try:
            validate_smtp_config(smtp_host, smtp_user, smtp_password, app_env)
        except ValidationError as e:
            validation_errors.append(str(e))
    
    # MinIO Configuration
    if minio_user != "" or minio_password != "":
        try:
            validate_minio_config(minio_user, minio_password, app_env)
        except ValidationError as e:
            validation_errors.append(str(e))
    
    # GitHub OAuth
    if github_client_id != "" or github_client_secret != "":
        try:
            validate_github_oauth(github_client_id, github_client_secret, app_env)
        except ValidationError as e:
            validation_errors.append(str(e))
    
    # Google OAuth
    if google_client_id != "" or google_client_secret != "":
        try:
            validate_google_oauth(google_client_id, google_client_secret, app_env)
        except ValidationError as e:
            validation_errors.append(str(e))
    
    # SAML Configuration
    try:
        validate_saml_config(saml_enabled, saml_metadata_url, saml_cert_path, saml_key_path, app_env)
    except ValidationError as e:
        validation_errors.append(str(e))
    
    # CORS Origins
    validate_cors_origins(cors_origins)
    
    # Redis URL
    validate_redis_url(redis_url, app_env)
    
    # OpenAI API Key
    validate_openai_api_key(openai_key, app_env)
    
    # If any production errors, raise
    if validation_errors:
        raise ValidationError("\n".join(validation_errors))
    
    # Print warnings for development
    if warnings:
        print(
            f"WARNING: Missing environment variables in {app_env} mode: "
            f"{', '.join(sorted(warnings))}",
            file=sys.stderr
        )
    
    return len(validation_errors) == 0


class ValidationResult:
    """Result of configuration validation."""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []


def validate_config(settings) -> ValidationResult:
    """Validate configuration and return validation result.
    
    Args:
        settings: Settings dataclass instance
    
    Returns:
        ValidationResult with errors and warnings lists
    """
    app_env = settings.app_env
    result = ValidationResult()
    
    # Get all environment values from settings
    db_url = settings.database_url
    jwt_secret = settings.jwt_secret
    session_secret = ""  # SESSION_SECRET not in settings, skip
    encryption_key = settings.encryption_key
    cors_origins = settings.cors_origins
    
    postgres_user = get_env_value("POSTGRES_USER")
    postgres_password = get_env_value("POSTGRES_PASSWORD")
    
    smtp_host = get_env_value("SMTP_HOST")
    smtp_user = get_env_value("SMTP_USERNAME")
    smtp_password = get_env_value("SMTP_PASSWORD")
    
    minio_user = get_env_value("MINIO_ROOT_USER")
    minio_password = get_env_value("MINIO_ROOT_PASSWORD")
    
    github_client_id = get_env_value("GITHUB_OAUTH2_CLIENT_ID")
    github_client_secret = get_env_value("GITHUB_OAUTH2_CLIENT_SECRET")
    
    google_client_id = get_env_value("GOOGLE_OAUTH2_CLIENT_ID")
    google_client_secret = get_env_value("GOOGLE_OAUTH2_CLIENT_SECRET")
    
    saml_enabled = get_env_value("ENABLE_SAML")
    saml_metadata_url = get_env_value("SAML_METADATA_URL")
    saml_cert_path = get_env_value("SAML_CERT_PATH")
    saml_key_path = get_env_value("SAML_KEY_PATH")
    
    redis_url = get_env_value("REDIS_URL")
    openai_key = get_env_value("OPENAI_API_KEY")
    
    # Run all validations and collect errors/warnings
    # JWT Secret
    try:
        validate_jwt_secret(jwt_secret, app_env)
    except ValidationError as e:
        result.errors.append(str(e))
    
    # Encryption Key - already validated during Settings creation, skip here
    
    # Database URL
    try:
        validate_database_url(db_url, app_env)
    except ValidationError as e:
        result.errors.append(str(e))
    
    # PostgreSQL credentials
    using_db_url = db_url.startswith("postgresql://")
    if db_url.startswith("postgresql://"):
        try:
            validate_database_credentials(postgres_user, postgres_password, app_env, using_db_url)
        except ValidationError as e:
            result.errors.append(str(e))
    
    # SMTP Configuration
    if smtp_host != "":
        try:
            validate_smtp_config(smtp_host, smtp_user, smtp_password, app_env)
        except ValidationError as e:
            result.errors.append(str(e))
    
    # MinIO Configuration
    if minio_user != "" or minio_password != "":
        try:
            validate_minio_config(minio_user, minio_password, app_env)
        except ValidationError as e:
            result.errors.append(str(e))
    
    # GitHub OAuth
    if github_client_id != "" or github_client_secret != "":
        try:
            validate_github_oauth(github_client_id, github_client_secret, app_env)
        except ValidationError as e:
            result.errors.append(str(e))
    
    # Google OAuth
    if google_client_id != "" or google_client_secret != "":
        try:
            validate_google_oauth(google_client_id, google_client_secret, app_env)
        except ValidationError as e:
            result.errors.append(str(e))
    
    # SAML Configuration
    try:
        validate_saml_config(saml_enabled, saml_metadata_url, saml_cert_path, saml_key_path, app_env)
    except ValidationError as e:
        result.errors.append(str(e))
    
    # CORS Warnings
    if validate_cors_origins(cors_origins):
        result.warnings.append("CORS validation warning (see logs)")
    
    # Redis Warnings
    if validate_redis_url(redis_url, app_env):
        result.warnings.append("Redis URL validation warning (see logs)")
    
    # OpenAI API Key Warnings
    if validate_openai_api_key(openai_key, app_env):
        result.warnings.append("OpenAI API key warning (see logs)")
    
    return result


def main() -> int:
    """Main entry point for validation CLI."""
    try:
        run_validations()
        print("Environment validation passed.")
        return 0
    except ValidationError as e:
        print(f"Environment validation failed:\n{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during validation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
