"""
Tests for Secret Containment and Environment Security.

Enforces that:
1. No live environment files (.env, .env.development, .env.production, etc.) are tracked.
2. Example templates remain tracked and safe.
3. Production configuration fails safely when secrets are missing, weak, or placeholders.
4. Development/testing environments remain functional with secure fallback generation.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import (
    Settings,
    _resolve_jwt_secret,
    _resolve_encryption_key,
)
from app.config_validation import ConfigValidator


REPO_ROOT = Path(__file__).resolve().parents[2]


class TestSecretContainmentInGit:
    """Ensure sensitive environment files are excluded from Git version control."""

    def test_untracked_environment_files(self):
        """Verify that no real environment files are tracked by Git."""
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        tracked = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]

        forbidden_basenames = {
            ".env",
            ".env.development",
            ".env.production",
            ".env.staging",
            ".env.local",
            ".env.test.local",
            ".env.development.local",
            ".env.production.local",
        }

        for path in tracked:
            base = os.path.basename(path)
            assert base not in forbidden_basenames, (
                f"Security exposure: Real environment file '{path}' is tracked in Git index!"
            )

    def test_safe_templates_remain_tracked(self):
        """Verify that documented example templates remain tracked in Git."""
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        tracked = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]

        required_templates = [
            ".env.example",
            "backend/.env.example",
            "frontend/.env.example",
        ]
        for template in required_templates:
            assert template in tracked, f"Required template '{template}' is missing from Git tracking!"

    def test_gitignore_blocks_real_env_files(self):
        """Verify git check-ignore properly ignores real environment files."""
        candidates = [
            ".env",
            ".env.development",
            ".env.production",
            ".env.local",
            "frontend/.env.production",
        ]
        for candidate in candidates:
            res = subprocess.run(
                ["git", "check-ignore", "-q", candidate],
                cwd=str(REPO_ROOT),
                capture_output=True,
            )
            assert res.returncode == 0, f"Git failed to ignore '{candidate}'!"

    def test_templates_do_not_contain_live_secrets(self):
        """Verify templates contain no live private keys, tokens, or live API keys."""
        templates = [
            REPO_ROOT / ".env.example",
            REPO_ROOT / "backend/.env.example",
            REPO_ROOT / "frontend/.env.example",
        ]
        prohibited_markers = [
            "BEGIN RSA PRIVATE KEY",
            "BEGIN EC PRIVATE KEY",
            "BEGIN PRIVATE KEY",
            "ghp_",
            "AKIA",
            "AIza",
        ]
        for template_path in templates:
            assert template_path.exists(), f"Template '{template_path}' must exist"
            content = template_path.read_text(encoding="utf-8")
            for marker in prohibited_markers:
                assert marker not in content, (
                    f"Template '{template_path.name}' contains forbidden secret signature: {marker}"
                )


class TestConfigSecurityValidation:
    """Ensure settings validation prevents predictable or missing secrets in production."""

    def test_production_jwt_secret_required(self):
        """In production, missing JWT_SECRET must raise ValueError."""
        with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": ""}, clear=False):
            with pytest.raises(ValueError, match="JWT_SECRET environment variable is required in production"):
                _resolve_jwt_secret()

    def test_production_jwt_secret_min_length(self):
        """In production, short JWT_SECRET must raise ValueError."""
        with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": "too-short"}, clear=False):
            with pytest.raises(ValueError, match="at least 32 characters"):
                _resolve_jwt_secret()

    def test_production_jwt_secret_rejects_placeholders(self):
        """In production, placeholder JWT_SECRET must raise ValueError."""
        placeholders = [
            "replace-with-a-secure-random-secret-at-least-32-chars-long",
            "change-this-to-a-random-secret-in-production",
            "your-secret-key-here-change-in-production",
        ]
        for ph in placeholders:
            with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": ph}, clear=False):
                with pytest.raises(ValueError, match="insecure placeholder"):
                    _resolve_jwt_secret()

    def test_production_jwt_secret_valid(self):
        """In production, a strong random 32+ character secret succeeds."""
        strong_secret = "k" * 48
        with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": strong_secret}, clear=False):
            assert _resolve_jwt_secret() == strong_secret

    def test_development_jwt_secret_fallback(self):
        """In development, missing JWT_SECRET safely generates an ephemeral random secret."""
        with patch.dict(os.environ, {"APP_ENV": "development", "JWT_SECRET": ""}, clear=False):
            gen = _resolve_jwt_secret()
            assert len(gen) == 64  # token_hex(32)

    def test_production_encryption_key_rejects_placeholders(self):
        """In production, placeholder ENCRYPTION_KEY must raise ValueError."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "ENCRYPTION_KEY": "replace-with-a-secure-random-secret-at-least-32-chars-long",
            },
            clear=False,
        ):
            with pytest.raises(ValueError, match="insecure placeholder"):
                _resolve_encryption_key()

    def test_config_validator_catches_insecure_production_settings(self):
        """ConfigValidator flags missing/placeholder secrets in production as errors."""
        valid_jwt = "v" * 48
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "JWT_SECRET": valid_jwt,
                "ENCRYPTION_KEY": "",
            },
            clear=False,
        ):
            settings = Settings()
            validator = ConfigValidator(settings)
            result = validator.validate_all()
            assert not result.is_valid
            assert any("ENCRYPTION_KEY" in err for err in result.errors)
