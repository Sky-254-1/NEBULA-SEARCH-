"""Application configuration loaded from environment variables."""

import os
import secrets
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if secret:
        if os.getenv("APP_ENV", "development") == "production" and len(secret) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters in production. "
                f"Current length: {len(secret)} characters."
            )
        return secret
    generated = secrets.token_hex(32)
    if os.getenv("APP_ENV", "development") == "production":
        print(
            "WARNING: JWT_SECRET is not set in production. "
            "Tokens will be invalidated on restart.",
            file=sys.stderr,
        )
    return generated


def _resolve_encryption_key() -> bytes:
    raw = os.getenv("ENCRYPTION_KEY", "")
    if raw:
        return raw.encode("utf-8")
    if os.getenv("APP_ENV", "development") == "production":
        print(
            "WARNING: ENCRYPTION_KEY is not set in production. "
            "Data at rest will use a derived key.",
            file=sys.stderr,
        )
    return secrets.token_bytes(32)


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings for Nebula Search API."""

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "nebula.db"))
    jwt_secret: str = field(default_factory=_resolve_jwt_secret)
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    )
    jwt_expiry_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_MINUTES", "30"))
    )
    refresh_token_days: int = field(
        default_factory=lambda: int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
    )
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))
    gguf_model_path: str = field(default_factory=lambda: os.getenv("GGUF_MODEL_PATH", ""))
    ai_provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "auto"))
    brave_api_key: str = field(default_factory=lambda: os.getenv("BRAVE_API_KEY", ""))
    serpapi_key: str = field(default_factory=lambda: os.getenv("SERPAPI_KEY", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    elasticsearch_url: str = field(default_factory=lambda: os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"))
    rabbitmq_url: str = field(default_factory=lambda: os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))
    kafka_bootstrap_servers: str = field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    )
    cors_origins: str = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        )
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins into a list.

        A literal ``*`` is rejected because ``allow_credentials=True`` is set
        in the CORS middleware — combining wildcard origins with credentials
        is invalid per the CORS spec and silently fails in most browsers.
        """
        raw = self.cors_origins.strip()
        if raw == "*":
            raise ValueError(
                "CORS_ORIGINS='*' is not allowed when allow_credentials=True. "
                "Set CORS_ORIGINS to an explicit allow-list of origins."
            )
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    cache_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300"))
    )
    storage_root: str = field(
        default_factory=lambda: os.getenv("STORAGE_ROOT", str(_REPO_ROOT / "storage"))
    )

    # Security & Auth
    auth_cookie_mode: bool = field(
        default_factory=lambda: os.getenv("AUTH_COOKIE_MODE", "true").lower() == "true"
    )
    cookie_secure: bool = field(
        default_factory=lambda: os.getenv("COOKIE_SECURE", "true").lower() == "true"
    )
    cookie_samesite: str = field(
        default_factory=lambda: os.getenv("COOKIE_SAMESITE", "lax")
    )
    enable_rbac: bool = field(
        default_factory=lambda: os.getenv("ENABLE_RBAC", "true").lower() == "true"
    )
    enable_refresh_reuse_detection: bool = field(
        default_factory=lambda: os.getenv("ENABLE_REFRESH_REUSE_DETECTION", "true").lower() == "true"
    )
    enable_audit_logs: bool = field(
        default_factory=lambda: os.getenv("ENABLE_AUDIT_LOGS", "true").lower() == "true"
    )

    # Brute-force protection
    max_login_attempts: int = field(
        default_factory=lambda: int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    )
    login_lockout_minutes: int = field(
        default_factory=lambda: int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
    )
    signup_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("SIGNUP_RATE_LIMIT", "5"))
    )
    login_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("LOGIN_RATE_LIMIT", "5"))
    )
    refresh_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("REFRESH_RATE_LIMIT", "10"))
    )

    # === Content Security Policy ===
    csp_default_src: str = field(
        default_factory=lambda: os.getenv("CSP_DEFAULT_SRC", "'self'")
    )
    csp_script_src: str = field(
        default_factory=lambda: os.getenv("CSP_SCRIPT_SRC", "'self'")
    )
    csp_style_src: str = field(
        default_factory=lambda: os.getenv("CSP_STYLE_SRC", "'self'")
    )
    csp_img_src: str = field(
        default_factory=lambda: os.getenv("CSP_IMG_SRC", "'self' data:")
    )
    csp_connect_src: str = field(
        default_factory=lambda: os.getenv("CSP_CONNECT_SRC", "'self'")
    )
    csp_font_src: str = field(
        default_factory=lambda: os.getenv("CSP_FONT_SRC", "'self'")
    )
    csp_frame_src: str = field(
        default_factory=lambda: os.getenv("CSP_FRAME_SRC", "'none'")
    )
    csp_object_src: str = field(
        default_factory=lambda: os.getenv("CSP_OBJECT_SRC", "'none'")
    )
    csp_report_uri: str = field(
        default_factory=lambda: os.getenv("CSP_REPORT_URI", "")
    )

    # === Feature Flags ===
    enable_csrf: bool = field(
        default_factory=lambda: os.getenv("ENABLE_CSRF", "true").lower() == "true"
    )
    enable_2fa: bool = field(
        default_factory=lambda: os.getenv("ENABLE_2FA", "false").lower() == "true"
    )
    enable_webauthn: bool = field(
        default_factory=lambda: os.getenv("ENABLE_WEBAUTHN", "false").lower() == "true"
    )
    require_email_verification: bool = field(
        default_factory=lambda: os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"
    )

    # === 2FA / TOTP ===
    totp_issuer: str = field(
        default_factory=lambda: os.getenv("TOTP_ISSUER", "Nebula Search")
    )
    jwt_issuer: str = field(
        default_factory=lambda: os.getenv("JWT_ISSUER", "Nebula Search")
    )
    jwt_audience: str = field(
        default_factory=lambda: os.getenv("JWT_AUDIENCE", "nebula-search-api")
    )

    # === Encryption Key for data at rest ===
    encryption_key: bytes = field(default_factory=_resolve_encryption_key)

    # === OAuth2 / SSO ===
    google_oauth2_client_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_OAUTH2_CLIENT_ID", "")
    )
    google_oauth2_client_secret: str = field(
        default_factory=lambda: os.getenv("GOOGLE_OAUTH2_CLIENT_SECRET", "")
    )
    github_oauth2_client_id: str = field(
        default_factory=lambda: os.getenv("GITHUB_OAUTH2_CLIENT_ID", "")
    )
    github_oauth2_client_secret: str = field(
        default_factory=lambda: os.getenv("GITHUB_OAUTH2_CLIENT_SECRET", "")
    )
    oauth2_redirect_base_uri: str = field(
        default_factory=lambda: os.getenv("OAUTH2_REDIRECT_BASE_URI", "http://localhost:8000/api/v1/auth/oauth2")
    )
    oauth2_frontend_redirect_uri: str = field(
        default_factory=lambda: os.getenv("OAUTH2_FRONTEND_REDIRECT_URI", "http://localhost:5173/oauth/callback")
    )

    # === SAML 2.0 SSO ===
    enable_saml: bool = field(
        default_factory=lambda: os.getenv("ENABLE_SAML", "false").lower() == "true"
    )
    saml_entity_id: str = field(
        default_factory=lambda: os.getenv("SAML_ENTITY_ID", "nebula-search")
    )
    saml_metadata_url: str = field(
        default_factory=lambda: os.getenv("SAML_METADATA_URL", "")
    )
    saml_cert_path: str = field(
        default_factory=lambda: os.getenv("SAML_CERT_PATH", "")
    )
    saml_key_path: str = field(
        default_factory=lambda: os.getenv("SAML_KEY_PATH", "")
    )

    # === Biometric Authentication (WebAuthn) ===
    enable_webauthn: bool = field(
        default_factory=lambda: os.getenv("ENABLE_WEBAUTHN", "false").lower() == "true"
    )
    webauthn_rp_id: str = field(
        default_factory=lambda: os.getenv("WEBAUTHN_RP_ID", "localhost")
    )
    webauthn_rp_name: str = field(
        default_factory=lambda: os.getenv("WEBAUTHN_RP_NAME", "Nebula Search")
    )

    # === Push Notifications ===
    enable_push_notifications: bool = field(
        default_factory=lambda: os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true"
    )
    fcm_server_key: str = field(
        default_factory=lambda: os.getenv("FCM_SERVER_KEY", "")
    )
    fcm_project_id: str = field(
        default_factory=lambda: os.getenv("FCM_PROJECT_ID", "")
    )
    apns_key_id: str = field(
        default_factory=lambda: os.getenv("APNS_KEY_ID", "")
    )
    apns_team_id: str = field(
        default_factory=lambda: os.getenv("APNS_TEAM_ID", "")
    )
    apns_bundle_id: str = field(
        default_factory=lambda: os.getenv("APNS_BUNDLE_ID", "com.nebula.search")
    )

    # === Document Preview ===
    enable_document_preview: bool = field(
        default_factory=lambda: os.getenv("ENABLE_DOCUMENT_PREVIEW", "true").lower() == "true"
    )
    max_preview_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_PREVIEW_SIZE_MB", "50"))
    )

    # === Federated Search ===
    enable_federated_search: bool = field(
        default_factory=lambda: os.getenv("ENABLE_FEDERATED_SEARCH", "false").lower() == "true"
    )
    federated_search_devices: str = field(
        default_factory=lambda: os.getenv("FEDERATED_SEARCH_DEVICES", "")
    )

    # === Plugin System ===
    enable_plugin_system: bool = field(
        default_factory=lambda: os.getenv("ENABLE_PLUGIN_SYSTEM", "false").lower() == "true"
    )
    plugin_directory: str = field(
        default_factory=lambda: os.getenv("PLUGIN_DIRECTORY", str(_REPO_ROOT / "plugins"))
    )

    # === Email/SMTP Settings ===
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: str = field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    smtp_from_email: str = field(default_factory=lambda: os.getenv("SMTP_FROM_EMAIL", ""))
    smtp_from_name: str = field(default_factory=lambda: os.getenv("SMTP_FROM_NAME", "Nebula Search"))
    smtp_use_tls: bool = field(
        default_factory=lambda: os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    )
    email_verification_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("EMAIL_VERIFICATION_EXPIRY_HOURS", "24"))
    )
    password_reset_expiry_hours: int = field(
        default_factory=lambda: int(os.getenv("PASSWORD_RESET_EXPIRY_HOURS", "1"))
    )

    # === API Key Settings ===
    api_key_length: int = field(
        default_factory=lambda: int(os.getenv("API_KEY_LENGTH", "32"))
    )
    api_key_prefix: str = field(
        default_factory=lambda: os.getenv("API_KEY_PREFIX", "nb_")
    )

    # === Observability: Sentry ===
    sentry_dsn: str = field(default_factory=lambda: os.getenv("SENTRY_DSN", ""))

    # === Observability: OpenTelemetry ===
    otel_service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "nebula-search")
    )
    otel_exporter_otlp_endpoint: str = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    )

    # === Logging ===
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO" if os.getenv("APP_ENV", "development") == "production" else "DEBUG")
    )
    log_json_format: bool = field(
        default_factory=lambda: os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    )

    # === Rate Limit Tiers (requests per minute) ===
    rate_limit_tier_basic: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_TIER_BASIC", "30"))
    )
    rate_limit_tier_pro: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_TIER_PRO", "120"))
    )
    rate_limit_tier_enterprise: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_TIER_ENTERPRISE", "600"))
    )
    rate_limit_burst_multiplier: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_BURST_MULTIPLIER", "2"))
    )

    # === Cross-Origin Headers ===
    cross_origin_embedder_policy: str = field(
        default_factory=lambda: os.getenv("CROSS_ORIGIN_EMBEDDER_POLICY", "require-corp")
    )
    cross_origin_opener_policy: str = field(
        default_factory=lambda: os.getenv("CROSS_ORIGIN_OPENER_POLICY", "same-origin")
    )
    cross_origin_resource_policy: str = field(
        default_factory=lambda: os.getenv("CROSS_ORIGIN_RESOURCE_POLICY", "same-origin")
    )

    # === Crawler Settings ===
    crawler_user_agent: str = field(
        default_factory=lambda: os.getenv("CRAWLER_USER_AGENT", "NebulaSearch/1.0")
    )
    crawler_max_concurrency: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_MAX_CONCURRENCY", "10"))
    )
    crawler_default_delay: float = field(
        default_factory=lambda: float(os.getenv("CRAWLER_DEFAULT_DELAY", "1.0"))
    )
    crawler_max_depth: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_MAX_DEPTH", "3"))
    )
    crawler_max_pages_per_job: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_MAX_PAGES_PER_JOB", "100"))
    )
    crawler_robots_ttl: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_ROBOTS_TTL", "86400"))
    )

    # === Permissions-Policy ===
    permissions_policy: str = field(
        default_factory=lambda: os.getenv(
            "PERMISSIONS_POLICY",
            "geolocation=(), microphone=(), camera=()",
        )
    )

    # === Admin IP Whitelist (comma-separated) ===
    admin_ip_whitelist: list[str] = field(
        default_factory=lambda: [
            ip.strip()
            for ip in os.getenv("ADMIN_IP_WHITELIST", "").split(",")
            if ip.strip()
        ]
    )

    # === Indexing System Settings ===
    indexing_max_queue_size: int = field(
        default_factory=lambda: int(os.getenv("INDEXING_MAX_QUEUE_SIZE", "10000"))
    )
    indexing_worker_count: int = field(
        default_factory=lambda: int(os.getenv("INDEXING_WORKER_COUNT", "2"))
    )
    indexing_max_retries: int = field(
        default_factory=lambda: int(os.getenv("INDEXING_MAX_RETRIES", "5"))
    )
    indexing_retry_base_delay: float = field(
        default_factory=lambda: float(os.getenv("INDEXING_RETRY_BASE_DELAY", "5.0"))
    )
    indexing_retry_backoff_multiplier: float = field(
        default_factory=lambda: float(os.getenv("INDEXING_RETRY_BACKOFF_MULTIPLIER", "3.0"))
    )
    indexing_chunk_size: int = field(
        default_factory=lambda: int(os.getenv("INDEXING_CHUNK_SIZE", "1000"))
    )
    indexing_chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("INDEXING_CHUNK_OVERLAP", "200"))
    )

    @property
    def uses_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def db_path(self) -> str:
        if self.uses_postgres:
            return self.database_url
        return self.database_url

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def storage_uploads(self) -> Path:
        return Path(self.storage_root) / "uploads"

    @property
    def storage_cache(self) -> Path:
        return Path(self.storage_root) / "cache"

    @property
    def storage_vector(self) -> Path:
        return Path(self.storage_root) / "vector"

    @property
    def storage_indexes(self) -> Path:
        return Path(self.storage_root) / "indexes"

    @property
    def storage_exports(self) -> Path:
        return Path(self.storage_root) / "exports"

    @property
    def csp_policy(self) -> str:
        directives = [
            f"default-src {self.csp_default_src}",
            f"script-src {self.csp_script_src}",
            f"style-src {self.csp_style_src}",
            f"img-src {self.csp_img_src}",
            f"connect-src {self.csp_connect_src}",
            f"font-src {self.csp_font_src}",
            f"frame-src {self.csp_frame_src}",
            f"object-src {self.csp_object_src}",
        ]
        if self.csp_report_uri:
            directives.append(f"report-uri {self.csp_report_uri}")
            directives.append(f"report-to {self.csp_report_uri}")
        return "; ".join(directives)

    @property
    def encryption_key_bytes(self) -> bytes:
        key = self.encryption_key
        if len(key) < 32:
            key = key.ljust(32, b"\0")
        return key[:32]

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins into a list.

        A literal ``*`` is rejected because ``allow_credentials=True`` is set
        in the CORS middleware — combining wildcard origins with credentials
        is invalid per the CORS spec and silently fails in most browsers.
        """
        raw = self.cors_origins.strip()
        if raw == "*":
            raise ValueError(
                "CORS_ORIGINS='*' is not allowed when allow_credentials=True. "
                "Set CORS_ORIGINS to an explicit allow-list of origins."
            )
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
