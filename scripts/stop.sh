#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"

echo "[Docker] Stopping all services..."
docker compose -f "$COMPOSE" -f "$DEV" down 2>/dev/null || docker compose -f "$COMPOSE" down 2>/dev/null || true
if [ -f "$PROD" ]; then
    docker compose -f "$COMPOSE" -f "$PROD" down 2>/dev/null || true
fi
echo "[Docker] Services stopped."
