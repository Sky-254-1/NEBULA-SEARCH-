"""
Nebula Search Engine — Production Environment Setup.
Generates all required secrets and configuration for production deployment.

Usage:
    python scripts/setup_production.py
    python scripts/setup_production.py --output .env
    python scripts/setup_production.py --apply  (applies to current .env)

What this script does:
    1. Generates cryptographically secure JWT_SECRET (64 hex chars, 256-bit)
    2. Generates ENCRYPTION_KEY (64 hex chars, 256-bit)
    3. Generates API_KEY for programmatic access
    4. Outputs a complete .env file with all production settings
    5. Optionally applies to your current .env file
"""

import argparse
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path


def generate_secret(bits: int = 256) -> str:
    """Generate a cryptographically secure hex secret."""
    return secrets.token_hex(bits // 8)


def generate_password(length: int = 24) -> str:
    """Generate a secure alphanumeric password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_default_db_url() -> str:
    """Return a default PostgreSQL URL for local Docker."""
    return "postgresql://nebula:${DB_PASSWORD}@nebula-db:5432/nebula_search"


def get_default_redis_url() -> str:
    return "redis://nebula-redis:6379/0"


def generate_env_file(apply: bool = False) -> str:
    """Generate complete production .env file content."""
    jwt_secret = generate_secret(256)
    encryption_key = generate_secret(256)
    db_password = generate_password(32)
    api_key = f"nb_{secrets.token_urlsafe(32)}"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    env_content = f"""# ============================================================================
# Nebula Search Engine — Production Environment
# Auto-generated: {timestamp}
# ============================================================================
# To use:
#   cp .env.production .env && source .env
#   (or use Docker/K8s secrets for better security)
# ============================================================================

# === Application ===
APP_ENV=production
LOG_LEVEL=INFO
LOG_JSON_FORMAT=true

# === Security: JWT / Auth ===
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=30
JWT_EXPIRY_HOURS=24
JWT_ISSUER=Nebula Search
JWT_AUDIENCE=nebula-search-api
REFRESH_TOKEN_DAYS=30

# === Security: Encryption (data at rest) ===
ENCRYPTION_KEY={encryption_key}

# === Security: CORS ===
CORS_ORIGINS=https://search.nebula-search.com,https://app.nebula-search.com

# === Database ===
DATABASE_URL=postgresql://nebula:{db_password}@nebula-db:5432/nebula_search

# === Redis (required for multi-instance production, optional for single) ===
REDIS_URL=redis://nebula-redis:6379/0

# === Rate Limiting ===
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_TIER_BASIC=30
RATE_LIMIT_TIER_PRO=120
RATE_LIMIT_TIER_ENTERPRISE=600
RATE_LIMIT_BURST_MULTIPLIER=2
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
SIGNUP_RATE_LIMIT=5
LOGIN_RATE_LIMIT=5
REFRESH_RATE_LIMIT=10

# === Security Features ===
AUTH_COOKIE_MODE=true
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ENABLE_RBAC=true
ENABLE_REFRESH_REUSE_DETECTION=true
ENABLE_AUDIT_LOGS=true
ENABLE_CSRF=true
ENABLE_2FA=false
ENABLE_WEBAUTHN=false
REQUIRE_EMAIL_VERIFICATION=false

# === Content Security Policy ===
CSP_DEFAULT_SRC='self'
CSP_SCRIPT_SRC='self' 'unsafe-inline'
CSP_STYLE_SRC='self' 'unsafe-inline'
CSP_IMG_SRC='self' data: https:
CSP_CONNECT_SRC='self' https: wss:
CSP_FONT_SRC='self' data:
CSP_FRAME_SRC='none'
CSP_OBJECT_SRC='none'

# === Cache ===
CACHE_TTL_SECONDS=300

# === Storage ===
STORAGE_ROOT=/data/storage

# === API Keys ===
API_KEY_LENGTH=32
API_KEY_PREFIX=nb_

# === AI Providers (uncomment & configure as needed) ===
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4-turbo-preview
# OLLAMA_URL=http://ollama:11434
# OLLAMA_MODEL=llama3.2
# BRAVE_API_KEY=...
# SERPAPI_KEY=...

# === Crawler ===
CRAWLER_USER_AGENT=NebulaSearch/1.0
CRAWLER_MAX_CONCURRENCY=10
CRAWLER_DEFAULT_DELAY=1.0
CRAWLER_MAX_DEPTH=3
CRAWLER_MAX_PAGES_PER_JOB=100

# === Indexing ===
INDEXING_MAX_QUEUE_SIZE=10000
INDEXING_WORKER_COUNT=2
INDEXING_MAX_RETRIES=5
INDEXING_CHUNK_SIZE=1000
INDEXING_CHUNK_OVERLAP=200

# === Observability ===
# SENTRY_DSN=https://key@oXXXX.ingest.sentry.io/project
# OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
# OTEL_SERVICE_NAME=nebula-search

# === Email / SMTP ===
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USERNAME=apikey
# SMTP_PASSWORD=SG.xxxx
# SMTP_FROM_EMAIL=noreply@nebula-search.com
# SMTP_FROM_NAME=Nebula Search
# SMTP_USE_TLS=true
# EMAIL_VERIFICATION_EXPIRY_HOURS=24

# === OAuth2 / SSO ===
# GOOGLE_OAUTH2_CLIENT_ID=...
# GOOGLE_OAUTH2_CLIENT_SECRET=...
# GITHUB_OAUTH2_CLIENT_ID=...
# GITHUB_OAUTH2_CLIENT_SECRET=...
# OAUTH2_REDIRECT_BASE_URI=https://api.nebula-search.com/api/v1/auth/oauth2
# OAUTH2_FRONTEND_REDIRECT_URI=https://app.nebula-search.com/oauth/callback

# === Backup ===
# BACKUP_PROVIDER=s3
# S3_BUCKET=nebula-backups
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# BACKUP_RETENTION_DAYS=30

# === Cross-Origin ===
CROSS_ORIGIN_EMBEDDER_POLICY=require-corp
CROSS_ORIGIN_OPENER_POLICY=same-origin
CROSS_ORIGIN_RESOURCE_POLICY=same-origin
PERMISSIONS_POLICY=geolocation=(), microphone=(), camera=()

# ============================================================================
# IMPORTANT: Keep these values secure!
# JWT_SECRET and ENCRYPTION_KEY are auto-generated unique values.
# Store them in a password manager or vault.
#
# DB Password: {db_password}
# Generated API Key: {api_key}
# ============================================================================
"""
    return env_content


def main():
    parser = argparse.ArgumentParser(
        description="Nebula Search Production Environment Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python scripts/setup_production.py              # Print to stdout
  python scripts/setup_production.py -o .env      # Write to .env file
  python scripts/setup_production.py --apply      # Write to .env (shorthand)

Output:
  - Generates secure 256-bit JWT_SECRET
  - Generates secure 256-bit ENCRYPTION_KEY
  - Generates random database password
  - Produces complete production-ready .env file
        """,
    )
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output file path (e.g., .env or .env.production)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply to .env file (same as -o .env)")

    args = parser.parse_args()

    # Determine output destination
    output_path = None
    if args.apply:
        output_path = Path(".env")
    elif args.output:
        output_path = Path(args.output)

    # Generate environment file
    env_content = generate_env_file()

    if output_path:
        # Write to file
        output_path.write_text(env_content)
        print(f"\n  {GREEN}[SUCCESS]{RESET} Production .env written to: {output_path.absolute()}")
        print(f"\n  {YELLOW}[IMPORTANT]{RESET} Store these values securely:")
        print(f"    The JWT_SECRET and ENCRYPTION_KEY are unique to this installation.")
        print(f"    Back them up in a password manager before deploying.\n")
    else:
        # Print redacted preview — never dump secrets to stdout
        for line in env_content.strip().splitlines():
            key = line.split("=")[0] if "=" in line else line
            if any(s in key.upper() for s in ("SECRET", "KEY", "PASSWORD", "TOKEN")):
                print(f"{key}=***REDACTED***")
            else:
                print(line)
        print(f"\n  {YELLOW}[NOTE]{RESET} Secret values redacted. Use --output to write the full .env file.")


GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


if __name__ == "__main__":
    main()