#!/usr/bin/env python3
"""
Automated Secret Exposure and Environment File Containment Checker for NEBULA-SEARCH.

This script enforces:
1. No real environment files (.env, .env.development, .env.production, etc.) are tracked by Git.
2. Required example templates remain tracked and intact.
3. Templates contain no high-entropy secrets, live API keys, or private keys.
4. .gitignore files properly ignore real environment files by default.

Reports violations with file and variable names only. Never prints secret values.
Exit code: 0 on success, 1 on failure.
"""

import math
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_TRACKED_PATTERNS = [
    re.compile(r"^(\.env|\.env\..+|.*[/\\].env|.*[/\\].env\..+)$"),
]

ALLOWED_TRACKED_FILES = {
    ".env.example",
    "backend/.env.example",
    "frontend/.env.example",
}

SAFE_PLACEHOLDER_SUBSTRINGS = [
    "replace-with",
    "placeholder",
    "example",
    "your-",
    "change-this",
    "change-me",
    "changeme",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "default",
    "postgres",
    "minioadmin",
    "admin",
    "nebula",
    "todo",
]

SECRET_VALUE_PATTERNS = [
    (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"ghp_[A-Za-z0-9_]{30,}"), "GitHub Personal Access Token"),
    (re.compile(r"gho_[A-Za-z0-9_]{30,}"), "GitHub OAuth Token"),
    (re.compile(r"glpat-[A-Za-z0-9_\-]{20,}"), "GitLab Access Token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9_]{10,}"), "Slack Token"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI Live Secret Key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API Key"),
]


def shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy for character string."""
    if not data:
        return 0.0
    entropy = 0.0
    for char in set(data):
        prob = data.count(char) / len(data)
        entropy -= prob * math.log2(prob)
    return entropy


def check_git_tracked_files() -> list[str]:
    """Check that no forbidden environment files are tracked in Git."""
    errors = []
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]
    except Exception as exc:
        return [f"Failed to execute git ls-files: {exc}"]

    # 1. Verify forbidden environment files are NOT tracked
    for f in tracked_files:
        base = os.path.basename(f)
        if base.startswith(".env") or f.endswith(".env"):
            if f not in ALLOWED_TRACKED_FILES:
                errors.append(f"Forbidden environment file tracked in Git index: {f}")

    # 2. Verify allowed templates ARE tracked
    for allowed in ALLOWED_TRACKED_FILES:
        if allowed not in tracked_files:
            errors.append(f"Required example template missing from Git index: {allowed}")

    return errors


def check_template_contents() -> list[str]:
    """Verify that templates contain only safe placeholders and no exposed credentials."""
    errors = []

    for template_rel in ALLOWED_TRACKED_FILES:
        template_path = REPO_ROOT / template_rel
        if not template_path.is_file():
            errors.append(f"Template file not found on disk: {template_rel}")
            continue

        try:
            content = template_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            errors.append(f"Could not read {template_rel}: {exc}")
            continue

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue

            # Check for high-confidence secret signatures
            for pattern, pattern_name in SECRET_VALUE_PATTERNS:
                if pattern.search(trimmed):
                    errors.append(
                        f"Template {template_rel}:{idx} matched prohibited secret pattern [{pattern_name}]"
                    )

            # Check key=value pairs for suspicious high-entropy secrets
            if "=" in trimmed:
                key, _, value = trimmed.partition("=")
                key = key.strip()
                val = value.strip().strip("'\"")

                if not val:
                    continue

                val_lower = val.lower()
                is_safe_placeholder = any(sub in val_lower for sub in SAFE_PLACEHOLDER_SUBSTRINGS)

                # Flag high-entropy strings without placeholder words
                if (
                    len(val) >= 20
                    and not is_safe_placeholder
                    and not val.startswith(("http://", "https://", "ws://", "wss://", "postgresql://", "redis://"))
                ):
                    entropy = shannon_entropy(val)
                    if entropy > 4.2:
                        errors.append(
                            f"Template {template_rel}:{idx} variable '{key}' has high entropy ({entropy:.2f}) "
                            f"without an unmistakable placeholder keyword"
                        )

    return errors


def check_gitignore_rules() -> list[str]:
    """Verify that .gitignore ignores real environment files."""
    errors = []
    gitignore_path = REPO_ROOT / ".gitignore"
    if not gitignore_path.is_file():
        return ["Root .gitignore not found"]

    content = gitignore_path.read_text(encoding="utf-8", errors="replace")

    # Ensure dangerous negation rules are NOT present
    for bad_rule in ["!.env.development", "!.env.production", "!.env.local"]:
        if bad_rule in content:
            errors.append(f"Root .gitignore contains prohibited negation rule: {bad_rule}")

    # Test git check-ignore behavior
    test_files = [".env", ".env.development", ".env.production", ".env.local", "frontend/.env.production"]
    for tf in test_files:
        try:
            res = subprocess.run(
                ["git", "check-ignore", "-q", tf],
                cwd=str(REPO_ROOT),
                capture_output=True,
            )
            if res.returncode != 0:
                errors.append(f"Git ignore check failed: {tf} is NOT ignored by gitignore rules")
        except Exception as exc:
            errors.append(f"Failed running git check-ignore for {tf}: {exc}")

    return errors


def main() -> int:
    print("=" * 60)
    print("NEBULA SEARCH: Secret Containment & Environment Audit")
    print("=" * 60)

    all_errors: list[str] = []

    print("[1/3] Checking Git index for tracked environment files...")
    git_errors = check_git_tracked_files()
    if git_errors:
        all_errors.extend(git_errors)
        print(f"  FAILED: {len(git_errors)} violation(s) found")
    else:
        print("  PASSED: No real environment files tracked; all templates tracked.")

    print("[2/3] Checking template contents for accidental secrets...")
    template_errors = check_template_contents()
    if template_errors:
        all_errors.extend(template_errors)
        print(f"  FAILED: {len(template_errors)} violation(s) found")
    else:
        print("  PASSED: Templates contain safe placeholders only.")

    print("[3/3] Checking .gitignore containment rules...")
    gitignore_errors = check_gitignore_rules()
    if gitignore_errors:
        all_errors.extend(gitignore_errors)
        print(f"  FAILED: {len(gitignore_errors)} violation(s) found")
    else:
        print("  PASSED: .gitignore properly isolates real environment files.")

    print("=" * 60)
    if all_errors:
        print(f"AUDIT FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  - {err}")
        return 1
    else:
        print("AUDIT SUCCESS: All secret containment checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
