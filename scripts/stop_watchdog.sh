#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/zhang/Desktop/agent-watchdog"
PID_FILE="$BASE_DIR/runtime/watchdog.pid"
LAUNCHER_PID_FILE="$BASE_DIR/runtime/launcher.pid"
CODEX_SESSION_PARSER_PID_FILE="$BASE_DIR/runtime/codex_session_parser.pid"

stop_pid_file() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      echo "已停止进程: $pid"
    fi
    rm -f "$pid_file"
  fi
}

stop_pid_file "$PID_FILE"
stop_pid_file "$LAUNCHER_PID_FILE"
stop_pid_file "$CODEX_SESSION_PARSER_PID_FILE"

while IFS= read -r pid; do
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "已停止 watchdog 进程: $pid"
  fi
done < <(ps -ef | grep "$BASE_DIR/scripts/watchdog.py start" | grep -v grep | awk '{print $2}')

while IFS= read -r pid; do
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "已停止 Codex session parser 进程: $pid"
  fi
done < <(ps -ef | grep "$BASE_DIR/scripts/codex_session_parser.py --watch" | grep -v grep | awk '{print $2}')

echo "watchdog 停止完成"
