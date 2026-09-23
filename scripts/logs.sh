#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"
SERVICE="${1:-}"
MODE="${2:-dev}"

if [ "$MODE" = "prod" ]; then
    OVERRIDE="$PROD"
else
    OVERRIDE="$DEV"
fi

echo "[Docker] Showing logs (tail 200)..."
if [ -n "$SERVICE" ]; then
    docker compose -f "$COMPOSE" -f "$OVERRIDE" logs --tail 200 "$SERVICE"
else
    docker compose -f "$COMPOSE" -f "$OVERRIDE" logs --tail 200
fi
