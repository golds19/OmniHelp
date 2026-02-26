#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root regardless of where the script is called from
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="$REPO_ROOT/services/backend"
FRONTEND_DIR="$REPO_ROOT/services/frontend/multirag"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RESET='\033[0m'

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $(jobs -p) 2>/dev/null || true
    wait 2>/dev/null || true
}

trap cleanup INT TERM

# Start backend
(
    cd "$BACKEND_DIR"
    uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload 2>&1 \
        | sed "s/^/$(printf "${BLUE}[backend]${RESET} ")/"
) &

echo -n "Waiting for backend"
until curl -sf http://localhost:8000/ping > /dev/null 2>&1; do
    printf "."
    sleep 1
done
echo " ready!"

# Start frontend
(
    cd "$FRONTEND_DIR"
    npm run dev 2>&1 \
        | sed "s/^/$(printf "${GREEN}[frontend]${RESET} ")/"
) &

echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both services."
echo ""

wait
