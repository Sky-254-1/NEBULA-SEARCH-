#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export APP_ENV="${APP_ENV:-production}"
export PYTHONPATH="${SCRIPT_DIR}"
export LOG_LEVEL="${LOG_LEVEL:-info}"

if [ -f .env.production ]; then
    set -a
    source .env.production
    set +a
fi

echo "=== Nebula Search Production Start ==="
echo "Environment: ${APP_ENV}"
echo "Workers per core: ${WORKERS_PER_CORE:-2} (max: ${MAX_WORKERS:-8})"
echo "Bind: ${GUNICORN_BIND:-0.0.0.0:8000}"
echo "========================================"

exec gunicorn app.main:app -c gunicorn.conf.py
