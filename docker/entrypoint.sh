#!/bin/bash
set -euo pipefail

echo "Starting Nebula Search Engine..."

APP_ENV="${APP_ENV:-production}"
USE_GUNICORN="${USE_GUNICORN:-1}"
if [ "$APP_ENV" != "production" ]; then
    USE_GUNICORN=0
fi

# ── Wait for PostgreSQL (skip when using SQLite) ────────────────────────────
if echo "${DATABASE_URL:-}" | grep -q "postgresql"; then
    echo "Waiting for PostgreSQL..."
    for i in $(seq 1 30); do
        if python -c "
import asyncio, asyncpg, os
async def chk():
    await asyncpg.connect(os.environ['DATABASE_URL'])
asyncio.run(chk())
" 2>/dev/null; then
            echo "PostgreSQL is ready"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "PostgreSQL connection failed after 30 attempts"
            exit 1
        fi
        echo "  attempt $i/30…"
        sleep 1
    done

    echo "Running database migrations..."
    cd /app
    python -m app.database.migrate upgrade head 2>/dev/null || \
        python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
    echo "Migrations completed"
else
    echo "Using SQLite — skipping PostgreSQL wait and migrations"
fi

# ── Wait for Redis (only if REDIS_URL is set) ───────────────────────────────
if [ -n "${REDIS_URL:-}" ]; then
    echo "Waiting for Redis..."
    for i in $(seq 1 30); do
        if python -c "
import redis, os
redis.from_url(os.environ['REDIS_URL']).ping()
" 2>/dev/null; then
            echo "Redis is ready"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "Redis not available after 30 attempts — continuing without cache"
            break
        fi
        echo "  attempt $i/30…"
        sleep 1
    done
else
    echo "REDIS_URL not set — running without distributed cache"
fi

mkdir -p /app/storage/uploads /app/storage/cache /app/storage/vector \
         /app/storage/indexes /app/storage/exports /app/logs

cd /app

if [ $# -gt 0 ]; then
    echo "Starting application with command: $*"
    exec env PYTHONPATH=/app "$@"
fi

if [ "$USE_GUNICORN" = "1" ] && command -v gunicorn >/dev/null 2>&1; then
    echo "Starting Gunicorn (${WORKERS_PER_CORE:-2} workers/core, max ${MAX_WORKERS:-4})..."
    GUNICORN_CONF=""
    if [ -f /app/gunicorn.conf.py ]; then
        GUNICORN_CONF="-c /app/gunicorn.conf.py"
    elif [ -f /app/backend/gunicorn.conf.py ]; then
        GUNICORN_CONF="-c /app/backend/gunicorn.conf.py"
    fi
    exec env PYTHONPATH=/app gunicorn app.main:app \
        ${GUNICORN_CONF} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --workers "${WEB_CONCURRENCY:-$(python -c "import os; print(max(2, min(int(os.environ.get('MAX_WORKERS', 4)), os.cpu_count() * int(os.environ.get('WORKERS_PER_CORE', 2)))))")}" \
        --timeout 120 \
        --graceful-timeout 60 \
        --keep-alive 5 \
        --max-requests 10000 \
        --max-requests-jitter 1000 \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL:-info}"
else
    echo "Starting Uvicorn server..."
    exec env PYTHONPATH=/app uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level "${LOG_LEVEL:-info}" \
        --proxy-headers \
        --forwarded-allow-ips '*'
fi
