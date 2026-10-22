#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"

echo "[Docker] Running backend tests in container..."
docker compose -f "$COMPOSE" -f "$DEV" exec -T backend pytest /app/tests -v
echo "[Docker] Tests completed."
