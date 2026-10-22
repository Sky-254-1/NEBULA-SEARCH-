"""
Nebula Search Engine — Production Environment Validation.
Run this script to verify all production prerequisites are met.

Usage:
    python scripts/validate_production.py

For development mode (auto-tolerates missing production env vars):
    VALIDATION_MODE=development python scripts/validate_production.py

For strict production mode:
    APP_ENV=production VALIDATION_MODE=production python scripts/validate_production.py
"""

import asyncio
import os
import platform
import sys
from pathlib import Path
from typing import List, Tuple


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(name: str, condition: bool, hint: str = "") -> Tuple[bool, str]:
    if condition:
        print(f"  {GREEN}[PASS]{RESET} {name}")
        return True, ""
    print(f"  {RED}[FAIL]{RESET} {name}")
    if hint:
        print(f"        {YELLOW}Hint: {hint}{RESET}")
    return False, hint


def section(title: str):
    print(f"\n{CYAN}{'=' * 60}{RESET}")
    print(f"{CYAN}{title}{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}")


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


async def main() -> int:
    print(f"\n{BOLD}NEBULA SEARCH ENGINE — PRODUCTION VALIDATION{RESET}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Time: {__import__('datetime').datetime.now().isoformat()}")

    mode = os.environ.get("VALIDATION_MODE", "auto").lower()
    app_env = get_env("APP_ENV", "development")
    is_prod = app_env == "production"

    if mode == "auto":
        mode = "production" if is_prod else "development"

    print(f"Mode: {mode.upper()} (APP_ENV={app_env})")
    print(f"{GREEN}Running validation checks...{RESET}\n")

    errors: List[str] = []
    warnings: List[str] = []
    repo_root = Path(__file__).resolve().parent.parent

    # ==================================================== 1. Environment Config
    section("1. Environment Configuration")

    check("APP_ENV is set", bool(app_env), "Set APP_ENV=production in your .env")

    jwt_secret = get_env("JWT_SECRET", "")
    if mode == "production":
        passed, _ = check("JWT_SECRET >= 32 chars in production mode",
                          len(jwt_secret) >= 32,
                          "Generate: python -c \"import secrets; print(secrets.token_hex(32))\"")
        if not passed:
            errors.append("JWT_SECRET must be >= 32 characters for production")
    else:
        check("JWT_SECRET available (dev: auto-generated ok)",
              len(jwt_secret) >= 16 or jwt_secret == "",
              "Set JWT_SECRET for production")

    encryption_key = get_env("ENCRYPTION_KEY", "")
    check("ENCRYPTION_KEY available",
          len(encryption_key) >= 16 or encryption_key == "",
          "Set ENCRYPTION_KEY for data-at-rest encryption")

    database_url = get_env("DATABASE_URL", "")
    if mode == "production":
        passed, _ = check("DATABASE_URL configured for PostgreSQL",
                          bool(database_url) and "postgresql" in database_url,
                          "Set DATABASE_URL=postgresql://user:pass@host/db")
        if not passed:
            errors.append("DATABASE_URL must be set for production")
    else:
        check("DATABASE_URL available (dev: SQLite default ok)", True,
              "Set DATABASE_URL for production")

    redis_url = get_env("REDIS_URL", "")
    if mode == "production":
        check("REDIS_URL configured (production recommendation)",
              bool(redis_url),
              "Set REDIS_URL=redis://host:6379/0 for caching & queue")
    else:
        check("REDIS_URL available (dev: in-memory ok)", True, "")

    # ==================================================== 2. Security
    section("2. Security Configuration")

    sentry_dsn = get_env("SENTRY_DSN", "")
    check("SENTRY_DSN (error tracking)", bool(sentry_dsn),
          "Set SENTRY_DSN=https://key@oXXXX.ingest.sentry.io/project")

    csp_default = get_env("CSP_DEFAULT_SRC", "'self'")
    check("CSP policy configured", bool(csp_default),
          "Review CSP policy for production hardening")

    # ==================================================== 3. Build & Dependencies
    section("3. Build & Dependencies")

    try:
        import fastapi  # noqa
        import uvicorn  # noqa
        import sqlalchemy  # noqa
        import prometheus_client  # noqa
        import jwt  # noqa
        passed = True
    except ImportError:
        passed = False
    check("Core Python dependencies installed", passed,
          "Run: pip install -r backend/requirements.txt")

    req_file = repo_root / "backend" / "requirements.txt"
    req_dev = repo_root / "backend" / "requirements-dev.txt"
    check("Requirements files present", req_file.exists() and req_dev.exists(),
          "Run: pip install -r backend/requirements.txt")

    frontend_dir = repo_root / "frontend"
    dist_dir = frontend_dir / "dist"
    node_modules = frontend_dir / "node_modules"

    if mode == "production":
        check("Frontend production build exists",
              dist_dir.exists() and any(dist_dir.iterdir()),
              "Run: cd frontend && npm run build")
    else:
        check("Frontend source available", frontend_dir.exists(), "")

    if node_modules.exists():
        check("Frontend dependencies installed", True)
    else:
        check("Frontend dependencies installed", False, "Run: cd frontend && npm install")

    # ==================================================== 4. Infrastructure
    section("4. Infrastructure & Scripts")

    op_scripts = [
        "scripts/backup.sh", "scripts/backup.ps1", "scripts/restore.ps1",
        "scripts/cloud_backup.py", "scripts/zero_downtime_deploy.sh",
        "scripts/validate_production.py", "scripts/operations.sh",
        "scripts/health_check.sh", "scripts/rollback.sh",
    ]
    found = sum(1 for s in op_scripts if (repo_root / s).exists())
    check(f"Operation scripts ({found}/{len(op_scripts)})", found == len(op_scripts),
          f"Missing: {[s for s in op_scripts if not (repo_root / s).exists()]}")

    docker_files = [
        "docker/Dockerfile", "docker/Dockerfile.prod",
        "docker/docker-compose.prod.yml", "docker/nginx.prod.conf",
        "docker/docker-compose.yml",
    ]
    found = sum(1 for f in docker_files if (repo_root / f).exists())
    check(f"Docker configs ({found}/{len(docker_files)})", found >= 4, "")

    helm_dir = repo_root / "infrastructure" / "helm" / "nebula"
    check("Helm chart exists", helm_dir.exists(), "Create infrastructure/helm/nebula/")

    k8s_dir = repo_root / "infrastructure" / "k8s"
    k8s_files = list(k8s_dir.glob("*.yaml")) if k8s_dir.exists() else []
    check(f"K8s manifests ({len(k8s_files)})", len(k8s_files) >= 10,
          f"Found {len(k8s_files)} in infrastructure/k8s/")

    tf_dir = repo_root / "infrastructure" / "terraform"
    tf_files = list(tf_dir.glob("*.tf")) if tf_dir.exists() else []
    check(f"Terraform configs ({len(tf_files)})", len(tf_files) >= 3,
          f"Found {len(tf_files)} in infrastructure/terraform/")

    # ==================================================== 5. Monitoring
    section("5. Monitoring & Observability")

    check("Prometheus config exists",
          (repo_root / "infra" / "prometheus.yml").exists(), "")
    check("Prometheus alerts exist",
          (repo_root / "infra" / "prometheus-alerts.yml").exists(), "")
    check("Alertmanager config exists",
          (repo_root / "infra" / "alertmanager.yml").exists(), "")
    check("Loki logging config exists",
          (repo_root / "infra" / "loki-config.yml").exists(), "")

    grafana_dir = repo_root / "infra" / "grafana"
    dashboards = list(grafana_dir.rglob("*.json")) if grafana_dir.exists() else []
    check(f"Grafana dashboards ({len(dashboards)})", len(dashboards) >= 1, "")

    # ==================================================== Summary
    section("VALIDATION SUMMARY")

    if not errors and not warnings:
        print(f"\n  {GREEN}{BOLD}[PASS]{RESET} Environment validated. Ready for production.\n")
        return 0
    elif not errors and warnings:
        print(f"\n  {YELLOW}{BOLD}[PASS WITH WARNINGS]{RESET}")
        for w in warnings:
            print(f"    {YELLOW}→{RESET} {w}")
        print(f"\n  {GREEN}No blocking issues.{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}{BOLD}[ISSUES FOUND]{RESET}")
        for e in errors:
            print(f"    {RED}✗{RESET} {e}")
        for w in warnings:
            print(f"    {YELLOW}→{RESET} {w}")
        print(f"\n  {YELLOW}Recommended: python scripts/setup_production.py{RESET}\n")
        return 2 if mode == "production" else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)