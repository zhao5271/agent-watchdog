#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/zhang/Desktop/agent-watchdog"
PYTHON_BIN="${PYTHON_BIN:-python3}"

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

mkdir -p "$BASE_DIR/runtime"

# 单任务模式下，先停掉这个仓库里遗留的其他 watchdog 进程，避免多个写者同时覆盖状态文件。
bash "$BASE_DIR/scripts/stop_watchdog.sh" >/dev/null 2>&1 || true

# 每次启动前清理上一次运行留下的状态快照，避免读取到旧任务的残留状态。
rm -f \
  "$BASE_DIR/runtime/status.json" \
  "$BASE_DIR/runtime/events.log" \
  "$BASE_DIR/runtime/watchdog.pid" \
  "$BASE_DIR/runtime/launcher.pid" \
  "$BASE_DIR/runtime/watchdog.out.log" \
  "$BASE_DIR/runtime/watchdog.err.log"

nohup "$PYTHON_BIN" "$BASE_DIR/scripts/watchdog.py" start "$@" \
  >"$BASE_DIR/runtime/watchdog.out.log" 2>"$BASE_DIR/runtime/watchdog.err.log" &

WATCHDOG_PID=$!
echo "$WATCHDOG_PID" > "$BASE_DIR/runtime/launcher.pid"

echo "watchdog 已在后台启动"
echo "PID: $WATCHDOG_PID"
echo "状态文件: $BASE_DIR/runtime/status.json"
echo "事件日志: $BASE_DIR/runtime/events.log"
