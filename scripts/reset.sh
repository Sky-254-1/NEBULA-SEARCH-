#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.yml"
DEV="$ROOT/docker/docker-compose.dev.yml"
PROD="$ROOT/docker-compose.prod.yml"
MODE="${1:-dev}"

read -p "This will remove all volumes and recreate containers. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo "[Docker] Resetting environment..."
if [ "$MODE" = "prod" ]; then
    docker compose -f "$COMPOSE" -f "$PROD" down -v
else
    docker compose -f "$COMPOSE" -f "$DEV" down -v
fi
docker system prune -f
echo "[Docker] Reset complete. Run ./scripts/start.sh to restart."
