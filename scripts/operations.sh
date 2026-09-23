#!/usr/bin/env bash
# Nebula Search Engine — Operations Runbook entry point.
# Delegates to scripts/operations (deploy, rollback, backup, DR, etc.).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/operations" "$@"
