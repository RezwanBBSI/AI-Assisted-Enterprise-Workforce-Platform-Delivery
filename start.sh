#!/usr/bin/env bash
# start.sh — starts both the backend and frontend dev servers

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
  echo -e "\n${YELLOW}Shutting down servers...${NC}"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo -e "${GREEN}Done.${NC}"
}
trap cleanup INT TERM

# ── Backend ───────────────────────────────────────────────────────────────────
echo -e "${CYAN}[backend] Activating venv and starting FastAPI...${NC}"
source "$BACKEND/venv/bin/activate"

cd "$BACKEND"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}[backend] PID $BACKEND_PID — http://localhost:8000${NC}"

# ── Frontend ──────────────────────────────────────────────────────────────────
echo -e "${CYAN}[frontend] Installing deps (if needed) and starting Vite...${NC}"
cd "$FRONTEND"

if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}[frontend] node_modules not found — running npm install...${NC}"
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}[frontend] PID $FRONTEND_PID — http://localhost:5173${NC}"

# ── Wait ──────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}Both servers are running. Press Ctrl+C to stop.${NC}"
wait "$BACKEND_PID" "$FRONTEND_PID"
