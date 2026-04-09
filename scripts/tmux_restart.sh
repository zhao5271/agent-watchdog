#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/zhang/Desktop/agent-watchdog"
RUNTIME_DIR="$BASE_DIR/runtime"
TASK_RUNNER_SCRIPT="$BASE_DIR/scripts/tmux_task_runner.sh"
LAUNCH_FILE="$RUNTIME_DIR/launch.json"

ARCHIVE_SESSION=""
REASON="manual"

usage() {
  cat <<'EOF'
用法:
  bash /Users/zhang/Desktop/agent-watchdog/scripts/tmux_restart.sh \
    [--archive-session <旧session名>] \
    [--reason manual]
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --archive-session)
        ARCHIVE_SESSION="$2"
        shift 2
        ;;
      --reason)
        REASON="$2"
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

load_launch_metadata() {
  if [[ ! -f "$LAUNCH_FILE" ]]; then
    echo "未找到 launch.json"
    exit 1
  fi
}

archive_old_session() {
  local current_session target_session timestamp

  current_session="$ARCHIVE_SESSION"
  if [[ -z "$current_session" ]]; then
    current_session="$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/Users/zhang/Desktop/agent-watchdog/runtime/launch.json").read_text(encoding="utf-8"))
print(data.get("session_name", ""))
PY
)"
  fi

  if [[ -z "$current_session" ]]; then
    return
  fi

  if ! tmux has-session -t "$current_session" 2>/dev/null; then
    return
  fi

  timestamp="$(date '+%Y%m%d-%H%M%S')"
  target_session="$(CURRENT_SESSION_ENV="$current_session" TIMESTAMP_ENV="$timestamp" python3 - <<'PY'
import os
import re

session_name = os.environ["CURRENT_SESSION_ENV"]
timestamp = os.environ["TIMESTAMP_ENV"]
base = re.sub(r"-\d{8}-\d{6}$", "", session_name)
print(f"{base}-failed-{timestamp}")
PY
)"
  tmux rename-session -t "$current_session" "$target_session"
  echo "archived_session=$target_session"
}

create_replacement_session() {
  REASON_ENV="$REASON" python3 - <<'PY'
import json
import os
import base64
import shlex
from datetime import datetime
from pathlib import Path
import subprocess

base_dir = Path("/Users/zhang/Desktop/agent-watchdog")
runtime_dir = base_dir / "runtime"
launch_file = runtime_dir / "launch.json"
runner = base_dir / "scripts" / "tmux_task_runner.sh"
launch = json.loads(launch_file.read_text(encoding="utf-8"))

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
safe_task_id = "".join(ch.lower() if ch.isalnum() or ch in "-_" else "-" for ch in launch["task_id"]).strip("-") or "task"
session_name = f'{launch.get("session_prefix", "agent")}-{safe_task_id}-{timestamp}'
log_path = str(runtime_dir / f"{safe_task_id}-{timestamp}.log")
Path(log_path).write_text("", encoding="utf-8")

command_b64 = base64.b64encode(launch["command"].encode("utf-8")).decode("ascii")

subprocess.run(
    ["tmux", "new-session", "-d", "-s", session_name, f"TASK_COMMAND_B64={command_b64} bash '{runner}'"],
    check=True,
)
subprocess.run(["tmux", "set-option", "-t", session_name, "remain-on-exit", "on"], check=True, stdout=subprocess.DEVNULL)
pane_target = f"{session_name}:0.0"
subprocess.run(["tmux", "pipe-pane", "-o", "-t", pane_target, f"cat >> {shlex.quote(log_path)}"], check=True)
pane_id = subprocess.run(
    ["tmux", "display-message", "-p", "-t", pane_target, "#{pane_id}"],
    text=True,
    capture_output=True,
    check=True,
).stdout.strip()
pane_pid = subprocess.run(
    ["tmux", "display-message", "-p", "-t", pane_target, "#{pane_pid}"],
    text=True,
    capture_output=True,
    check=True,
).stdout.strip()

launch.update(
    {
        "log_path": log_path,
        "session_name": session_name,
        "window_index": "0",
        "pane_id": pane_id,
        "pane_pid": int(pane_pid or 0),
        "last_restart_reason": os.environ["REASON_ENV"],
    }
)
launch_file.write_text(json.dumps(launch, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"session_name": session_name, "pane_id": pane_id, "log_path": log_path}, ensure_ascii=False))
PY
}

parse_args "$@"
load_launch_metadata
archive_old_session >/dev/null
create_replacement_session
