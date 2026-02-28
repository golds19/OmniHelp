#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root regardless of where the script is called from
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="$REPO_ROOT/services/backend"
FRONTEND_DIR="$REPO_ROOT/services/frontend/multirag"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RESET='\033[0m'

BACKEND_LOG=$(mktemp)

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $(jobs -p) 2>/dev/null || true
    wait 2>/dev/null || true
    rm -f "$BACKEND_LOG"
}

trap cleanup INT TERM

# Start backend, capturing output to a log file while also writing to it
(
    cd "$BACKEND_DIR"
    uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload 2>&1 \
        | sed -u "s/^/$(printf "${BLUE}[backend]${RESET} ")/"
) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo -n "Waiting for backend"
while ! grep -q "Application startup complete" "$BACKEND_LOG" 2>/dev/null; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo " failed!"
        cat "$BACKEND_LOG"
        rm -f "$BACKEND_LOG"
        exit 1
    fi
    printf "."
    sleep 1
done
echo " ready!"
echo ""

# Show buffered backend startup logs
cat "$BACKEND_LOG"
echo ""

# Stream ongoing backend logs in the background
tail -f "$BACKEND_LOG" -n 0 &

# Start frontend only after backend is confirmed up
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
