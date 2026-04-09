#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/zhang/Desktop/agent-watchdog"
RUNTIME_DIR="$BASE_DIR/runtime"
START_WATCHDOG_SCRIPT="$BASE_DIR/scripts/start_watchdog.sh"
TASK_RUNNER_SCRIPT="$BASE_DIR/scripts/tmux_task_runner.sh"
LAUNCH_FILE="$RUNTIME_DIR/launch.json"

TASK_ID=""
TASK_NAME=""
TASK_COMMAND=""
LOG_PATH=""
SESSION_PREFIX="agent"
SOURCE="custom"
PROJECT=""
SOFT_TIMEOUT=300
HARD_TIMEOUT=900
POLL_INTERVAL=5
MAX_RESTARTS=3
STAGE_RULES="$BASE_DIR/config/stage-rules.json"

usage() {
  cat <<'EOF'
用法:
  bash /Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh \
    --task-id <任务ID> \
    --task-name <任务名称> \
    --command "<实际执行命令>" \
    [--log-path <日志文件路径>] \
    [--session-prefix agent] \
    [--soft-timeout 300] \
    [--hard-timeout 900] \
    [--poll-interval 5] \
    [--max-restarts 3] \
    [--source custom] \
    [--project ""]
EOF
}

sanitize_task_id() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9_-' '-'
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --task-id)
        TASK_ID="$2"
        shift 2
        ;;
      --task-name)
        TASK_NAME="$2"
        shift 2
        ;;
      --command)
        TASK_COMMAND="$2"
        shift 2
        ;;
      --log-path)
        LOG_PATH="$2"
        shift 2
        ;;
      --session-prefix)
        SESSION_PREFIX="$2"
        shift 2
        ;;
      --soft-timeout)
        SOFT_TIMEOUT="$2"
        shift 2
        ;;
      --hard-timeout)
        HARD_TIMEOUT="$2"
        shift 2
        ;;
      --poll-interval)
        POLL_INTERVAL="$2"
        shift 2
        ;;
      --max-restarts)
        MAX_RESTARTS="$2"
        shift 2
        ;;
      --source)
        SOURCE="$2"
        shift 2
        ;;
      --project)
        PROJECT="$2"
        shift 2
        ;;
      --stage-rules)
        STAGE_RULES="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "未知参数: $1"
        usage
        exit 1
        ;;
    esac
  done
}

require_args() {
  if [[ -z "$TASK_ID" || -z "$TASK_NAME" || -z "$TASK_COMMAND" ]]; then
    usage
    exit 1
  fi
}

create_session() {
  local safe_task_id timestamp session_name pane_target pane_id pane_pid command_b64 pipe_command

  safe_task_id="$(sanitize_task_id "$TASK_ID")"
  timestamp="$(date '+%Y%m%d-%H%M%S')"
  session_name="${SESSION_PREFIX}-${safe_task_id}-${timestamp}"

  mkdir -p "$RUNTIME_DIR"
  if [[ -z "$LOG_PATH" ]]; then
    LOG_PATH="$RUNTIME_DIR/${safe_task_id}-${timestamp}.log"
  fi
  : > "$LOG_PATH"

  command_b64="$(printf '%s' "$TASK_COMMAND" | base64 | tr -d '\n')"

  tmux new-session -d -s "$session_name" \
    "TASK_COMMAND_B64=$command_b64 bash '$TASK_RUNNER_SCRIPT'"
  tmux set-option -t "$session_name" remain-on-exit on >/dev/null

  pane_target="${session_name}:0.0"
  pipe_command="cat >> $(printf '%q' "$LOG_PATH")"
  tmux pipe-pane -o -t "$pane_target" "$pipe_command"

  pane_id="$(tmux display-message -p -t "$pane_target" '#{pane_id}')"
  pane_pid="$(tmux display-message -p -t "$pane_target" '#{pane_pid}')"

  TASK_ID_ENV="$TASK_ID" \
  TASK_NAME_ENV="$TASK_NAME" \
  TASK_COMMAND_ENV="$TASK_COMMAND" \
  LOG_PATH_ENV="$LOG_PATH" \
  SESSION_NAME_ENV="$session_name" \
  PANE_ID_ENV="$pane_id" \
  PANE_PID_ENV="$pane_pid" \
  SESSION_PREFIX_ENV="$SESSION_PREFIX" \
  SOFT_TIMEOUT_ENV="$SOFT_TIMEOUT" \
  HARD_TIMEOUT_ENV="$HARD_TIMEOUT" \
  POLL_INTERVAL_ENV="$POLL_INTERVAL" \
  MAX_RESTARTS_ENV="$MAX_RESTARTS" \
  SOURCE_ENV="$SOURCE" \
  PROJECT_ENV="$PROJECT" \
  STAGE_RULES_ENV="$STAGE_RULES" \
  LAUNCH_FILE_ENV="$LAUNCH_FILE" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

launch = {
    "task_id": os.environ["TASK_ID_ENV"],
    "task_name": os.environ["TASK_NAME_ENV"],
    "command": os.environ["TASK_COMMAND_ENV"],
    "log_path": os.environ["LOG_PATH_ENV"],
    "session_name": os.environ["SESSION_NAME_ENV"],
    "window_index": "0",
    "pane_id": os.environ["PANE_ID_ENV"],
    "pane_pid": int(os.environ["PANE_PID_ENV"] or 0),
    "session_prefix": os.environ["SESSION_PREFIX_ENV"],
    "soft_timeout_seconds": int(os.environ["SOFT_TIMEOUT_ENV"]),
    "hard_timeout_seconds": int(os.environ["HARD_TIMEOUT_ENV"]),
    "poll_interval_seconds": int(os.environ["POLL_INTERVAL_ENV"]),
    "max_restarts": int(os.environ["MAX_RESTARTS_ENV"]),
    "auto_restart": True,
    "source": os.environ["SOURCE_ENV"],
    "project": os.environ["PROJECT_ENV"],
    "stage_rules": os.environ["STAGE_RULES_ENV"],
}

Path(os.environ["LAUNCH_FILE_ENV"]).write_text(
    json.dumps(launch, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY

  bash "$START_WATCHDOG_SCRIPT" \
    --task-id "$TASK_ID" \
    --task-name "$TASK_NAME" \
    --pid "$pane_pid" \
    --log-path "$LOG_PATH" \
    --soft-timeout "$SOFT_TIMEOUT" \
    --hard-timeout "$HARD_TIMEOUT" \
    --poll-interval "$POLL_INTERVAL" \
    --restart-command "bash $BASE_DIR/scripts/tmux_restart.sh" \
    --source "$SOURCE" \
    --project "$PROJECT" \
    --stage-rules "$STAGE_RULES" \
    --tmux-session "$session_name" \
    --tmux-window "0" \
    --tmux-pane-id "$pane_id" \
    --auto-restart \
    --max-restarts "$MAX_RESTARTS"

  echo "tmux session: $session_name"
  echo "pane id: $pane_id"
  echo "log path: $LOG_PATH"
}

parse_args "$@"
require_args
create_session
