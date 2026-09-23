#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"
ENV="$ROOT/backend/.env"
MODE="${1:-dev}"

if ! command -v docker &>/dev/null; then
    echo "[Docker] Docker is not installed or not in PATH." >&2
    exit 1
fi

if [ ! -f "$ENV" ]; then
    echo "[Docker] backend/.env not found. Copying from backend/.env.example..."
    cp "$ROOT/backend/.env.example" "$ENV"
fi

if [ "$MODE" = "prod" ]; then
    echo "[Docker] Starting in PRODUCTION mode..."
    if [ ! -f "$PROD" ]; then
        echo "[Docker] docker-compose.prod.yml not found. Using base compose."
        docker compose -f "$COMPOSE" up -d
    else
        docker compose -f "$COMPOSE" -f "$PROD" up -d
    fi
else
    echo "[Docker] Starting in DEVELOPMENT mode..."
    DOCKER_BUILDKIT=1 docker compose -f "$COMPOSE" -f "$DEV" up -d --build
fi

echo "[Docker] Services started. Run ./scripts/logs.sh to see output."
