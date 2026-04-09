#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/zhang/Desktop/agent-watchdog"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SESSION_RUNTIME_DIR="$BASE_DIR/runtime"
ARGS=("$@")

for ((i = 0; i < ${#ARGS[@]}; i++)); do
  if [[ "${ARGS[$i]}" == "--runtime-dir" && $((i + 1)) -lt ${#ARGS[@]} ]]; then
    SESSION_RUNTIME_DIR="${ARGS[$((i + 1))]}"
  fi
done

CODEX_SESSION_PARSER_PID_FILE="$SESSION_RUNTIME_DIR/codex_session_parser.pid"
WATCHDOG_LAUNCHER_PID_FILE="$SESSION_RUNTIME_DIR/launcher.pid"

start_detached() {
  local pid_var_name="$1"
  local out_log="$2"
  local err_log="$3"
  shift 3

  if command -v setsid >/dev/null 2>&1; then
    nohup setsid "$@" </dev/null >"$out_log" 2>"$err_log" &
  else
    nohup "$@" </dev/null >"$out_log" 2>"$err_log" &
  fi
  local child_pid=$!
  printf -v "$pid_var_name" '%s' "$child_pid"
}

assert_running() {
  local pid="$1"
  local err_log="$2"
  local process_name="$3"

  sleep 0.2
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "$process_name 启动失败"
    if [[ -f "$err_log" ]]; then
      cat "$err_log"
    fi
    exit 1
  fi
}

if [[ $# -lt 4 ]]; then
  cat <<'EOF'
用法:
  bash /Users/zhang/Desktop/agent-watchdog/scripts/start_watchdog.sh \
    --task-id <任务ID> \
    --task-name <任务名称> \
    --pid <进程PID> \
    --log-path <日志文件路径> \
    [--tmux-session <session名>] \
    [--tmux-pane-id <pane id>] \
    [--auto-restart] \
    [--max-restarts 3] \
    [--soft-timeout 300] \
    [--hard-timeout 900] \
    [--poll-interval 5] \
    [--restart-command "<重启命令>"] \
    [--source custom] \
    [--project ""]
EOF
  exit 1
fi

mkdir -p "$SESSION_RUNTIME_DIR"

# 每次启动前清理上一次运行留下的状态快照，避免读取到旧任务的残留状态。
rm -f \
  "$SESSION_RUNTIME_DIR/status.json" \
  "$SESSION_RUNTIME_DIR/codex_session.json" \
  "$SESSION_RUNTIME_DIR/events.log" \
  "$SESSION_RUNTIME_DIR/watchdog.pid" \
  "$CODEX_SESSION_PARSER_PID_FILE" \
  "$WATCHDOG_LAUNCHER_PID_FILE" \
  "$SESSION_RUNTIME_DIR/codex_session_parser.out.log" \
  "$SESSION_RUNTIME_DIR/codex_session_parser.err.log" \
  "$SESSION_RUNTIME_DIR/watchdog.out.log" \
  "$SESSION_RUNTIME_DIR/watchdog.err.log"

start_detached WATCHDOG_PID \
  "$SESSION_RUNTIME_DIR/watchdog.out.log" \
  "$SESSION_RUNTIME_DIR/watchdog.err.log" \
  "$PYTHON_BIN" "$BASE_DIR/scripts/watchdog.py" start "$@"
echo "$WATCHDOG_PID" > "$WATCHDOG_LAUNCHER_PID_FILE"
assert_running "$WATCHDOG_PID" "$SESSION_RUNTIME_DIR/watchdog.err.log" "watchdog"

start_detached CODEX_SESSION_PARSER_PID \
  "$SESSION_RUNTIME_DIR/codex_session_parser.out.log" \
  "$SESSION_RUNTIME_DIR/codex_session_parser.err.log" \
  "$PYTHON_BIN" "$BASE_DIR/scripts/codex_session_parser.py" --watch --runtime-dir "$SESSION_RUNTIME_DIR"
echo "$CODEX_SESSION_PARSER_PID" > "$CODEX_SESSION_PARSER_PID_FILE"
assert_running "$CODEX_SESSION_PARSER_PID" "$SESSION_RUNTIME_DIR/codex_session_parser.err.log" "Codex session parser"

echo "watchdog 已在后台启动"
echo "PID: $WATCHDOG_PID"
echo "状态文件: $SESSION_RUNTIME_DIR/status.json"
echo "Codex 会话快照: $SESSION_RUNTIME_DIR/codex_session.json"
echo "事件日志: $SESSION_RUNTIME_DIR/events.log"
