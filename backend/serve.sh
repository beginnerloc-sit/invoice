#!/usr/bin/env bash
# Production runner for the FastAPI backend.
# Usage:
#   ./serve.sh start    # start in background
#   ./serve.sh stop     # stop
#   ./serve.sh restart  # stop + start
#   ./serve.sh status   # show pid + port
#   ./serve.sh logs     # tail the log file
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7000}"
WORKERS="${WORKERS:-2}"
PID_FILE="$DIR/server.pid"
LOG_DIR="$DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
VENV="$DIR/.venv"

mkdir -p "$LOG_DIR"

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

start() {
  free_port

  if [[ ! -d "$VENV" ]]; then
    echo "[serve] error: venv not found at $VENV" >&2
    exit 1
  fi

  # shellcheck disable=SC1091
  source "$VENV/bin/activate"

  echo "[serve] starting uvicorn on $HOST:$PORT (workers=$WORKERS)"
  nohup uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --log-level info \
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
  kill "$pid" 2>/dev/null || true
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
  stop)    stop ;;
  restart) stop || true; start ;;
  status)  status ;;
  logs)    tail -f "$LOG_FILE" ;;
  *)       echo "usage: $0 {start|stop|restart|status|logs}"; exit 1 ;;
esac
