#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"
MODE="${1:-dev}"

echo "[Docker] Building all Docker services ($MODE)..."
if [ "$MODE" = "prod" ]; then
    if [ -f "$PROD" ]; then
        DOCKER_BUILDKIT=1 docker compose -f "$COMPOSE" -f "$PROD" build --no-cache
    else
        DOCKER_BUILDKIT=1 docker compose -f "$COMPOSE" build --no-cache
    fi
else
    DOCKER_BUILDKIT=1 docker compose -f "$COMPOSE" -f "$DEV" build --no-cache
fi
echo "[Docker] Build completed successfully."
