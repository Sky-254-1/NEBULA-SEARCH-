#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"
MODE="${1:-dev}"

if [ "$MODE" = "prod" ]; then
    docker compose -f "$COMPOSE" -f "$PROD" exec -T backend python -m app.database.migrate
else
    docker compose -f "$COMPOSE" -f "$DEV" exec -T backend python -m app.database.migrate
fi

echo "[Docker] Migrations applied successfully."
