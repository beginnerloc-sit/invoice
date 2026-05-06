#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pids=()
cleanup() {
  echo
  echo "[stop] shutting down..."
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM EXIT

echo "[run] backend  -> http://localhost:8000"
( cd "$ROOT/backend" && source .venv/bin/activate && exec uvicorn main:app --reload --port 8000 ) &
pids+=($!)

echo "[run] frontend -> http://localhost:5173"
( cd "$ROOT/frontend" && exec npm run dev ) &
pids+=($!)

wait
