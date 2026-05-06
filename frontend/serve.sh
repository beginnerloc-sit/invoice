#!/usr/bin/env bash
# Production runner for the Vite-built frontend.
# Builds dist/ and serves it via `vite preview` (which proxies /api to the backend
# per the `preview` block in vite.config.js).
#
# Usage:
#   ./serve.sh start    # build (if needed) + start in background
#   ./serve.sh build    # rebuild dist/ only
#   ./serve.sh stop     # stop
#   ./serve.sh restart  # rebuild + restart
#   ./serve.sh status
#   ./serve.sh logs
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5000}"
PID_FILE="$DIR/server.pid"
LOG_DIR="$DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
DIST="$DIR/dist"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/invoice}"

mkdir -p "$LOG_DIR"

# Use sudo only if we're not root and sudo is available; otherwise run directly.
if [[ "$EUID" -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

free_port() {
  local pids
  pids="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "[serve] port $PORT busy (pid: $(echo $pids | tr '\n' ' ')) — killing"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 0.5
    pids="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      sleep 0.3
    fi
  fi
  rm -f "$PID_FILE"
}

build() {
  if [[ ! -d "$DIR/node_modules" ]]; then
    echo "[serve] error: node_modules missing — run 'npm install' first" >&2
    exit 1
  fi
  echo "[serve] building production bundle..."
  npm run build
  deploy
}

deploy() {
  if [[ ! -d "$DIST" ]]; then
    echo "[serve] error: $DIST does not exist — build first" >&2
    exit 1
  fi
  echo "[serve] deploying $DIST → $DEPLOY_DIR"
  $SUDO mkdir -p "$DEPLOY_DIR"
  if command -v rsync >/dev/null 2>&1; then
    $SUDO rsync -a --delete "$DIST/" "$DEPLOY_DIR/"
  else
    # rsync not installed — fall back to clean + copy
    $SUDO find "$DEPLOY_DIR" -mindepth 1 -delete
    $SUDO cp -R "$DIST/." "$DEPLOY_DIR/"
  fi
  echo "[serve] deployed."
}

start() {
  free_port

  if [[ ! -d "$DIST" ]]; then
    build
  fi

  echo "[serve] starting vite preview on $HOST:$PORT"
  nohup npx vite preview --host "$HOST" --port "$PORT" \
    >> "$LOG_FILE" 2>&1 &

  echo $! > "$PID_FILE"
  sleep 1

  if is_running; then
    echo "[serve] started (pid $(cat "$PID_FILE")) — logs: $LOG_FILE"
  else
    echo "[serve] failed to start — check $LOG_FILE" >&2
    rm -f "$PID_FILE"
    exit 1
  fi
}

stop() {
  if ! is_running; then
    echo "[serve] not running"
    rm -f "$PID_FILE"
    return 0
  fi
  pid="$(cat "$PID_FILE")"
  echo "[serve] stopping pid $pid"
  # kill the whole process group so any child node processes (vite preview spawns one) die too
  kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.25
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "[serve] forcing kill"
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  echo "[serve] stopped"
}

status() {
  if is_running; then
    echo "[serve] running (pid $(cat "$PID_FILE")) on $HOST:$PORT"
  else
    echo "[serve] not running"
    exit 1
  fi
}

case "${1:-start}" in
  start)   start ;;
  build)   build ;;
  deploy)  deploy ;;
  stop)    stop ;;
  restart) stop || true; build; start ;;
  status)  status ;;
  logs)    tail -f "$LOG_FILE" ;;
  *)       echo "usage: $0 {start|build|deploy|stop|restart|status|logs}"; exit 1 ;;
esac
