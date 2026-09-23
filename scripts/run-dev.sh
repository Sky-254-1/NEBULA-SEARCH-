#!/usr/bin/env bash
# Start Nebula backend and frontend dev servers
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting Nebula backend on :8000..."
cd "$ROOT/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend static server on :3000..."
cd "$ROOT/frontend"
python -m http.server 3000 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
