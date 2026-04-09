#!/usr/bin/env python3
"""最小可用的任务 watchdog。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path("/Users/zhang/Desktop/agent-watchdog")
RUNTIME_DIR = BASE_DIR / "runtime"
STATUS_FILE = RUNTIME_DIR / "status.json"
EVENTS_FILE = RUNTIME_DIR / "events.log"
PID_FILE = RUNTIME_DIR / "watchdog.pid"
LAUNCH_FILE = RUNTIME_DIR / "launch.json"
TMUX_RESTART_SCRIPT = BASE_DIR / "scripts" / "tmux_restart.sh"

EXIT_CODE_PATTERN = re.compile(r"__TASK_EXIT_CODE__=(\d+)")
SESSION_SUFFIX_PATTERN = re.compile(r"-\d{8}-\d{6}$")
RESTARTABLE_STATUSES = {"stalled", "stopped", "failed"}
RESTART_COOLDOWN_SECONDS = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def append_event(event_type: str, payload: dict[str, Any]) -> None:
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {"time": now_iso(), "type": event_type, **payload}
    with EVENTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def tail_text(path: str, max_lines: int = 20) -> list[str]:
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()
    return [line.rstrip("\n") for line in lines[-max_lines:]]


def infer_stage(lines: list[str], stage_rules: list[dict[str, Any]], previous_stage: str) -> str:
    recent_lines = [line.lower() for line in lines[-10:]]
    for line in reversed(recent_lines):
        for rule in reversed(stage_rules):
            for keyword in rule.get("keywords", []):
                if keyword.lower() in line:
                    return str(rule["stage"])
    return previous_stage


def build_stage_index(stage: str, stage_order: list[str]) -> int:
    try:
        return stage_order.index(stage)
    except ValueError:
        return 0


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def tmux_session_exists(session_name: str) -> bool:
    if not session_name:
        return False
    result = run_command(["tmux", "has-session", "-t", session_name])
    return result.returncode == 0


def get_tmux_pane_info(session_name: str, pane_id: str = "") -> dict[str, Any]:
    info = {
        "session_exists": False,
        "pane_found": False,
        "pane_dead": False,
        "session_name": session_name,
        "pane_id": pane_id,
        "window_index": "",
        "pane_pid": 0,
        "pane_current_command": "",
    }
    if not session_name or not tmux_session_exists(session_name):
        return info

    result = run_command(
        [
            "tmux",
            "list-panes",
            "-t",
            session_name,
            "-F",
            "#{session_name}\t#{window_index}\t#{pane_id}\t#{pane_pid}\t#{pane_dead}\t#{pane_current_command}",
        ]
    )
    if result.returncode != 0:
        return info

    info["session_exists"] = True
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 6:
            continue
        current_session, window_index, current_pane_id, pane_pid_text, pane_dead_text, current_command = parts
        if pane_id and current_pane_id != pane_id:
            continue
        info.update(
            {
                "session_name": current_session,
                "window_index": window_index,
                "pane_id": current_pane_id,
                "pane_pid": int(pane_pid_text or 0),
                "pane_dead": pane_dead_text == "1",
                "pane_found": True,
                "pane_current_command": current_command,
            }
        )
        return info

    return info


def capture_tmux_output(session_name: str, pane_id: str = "", max_lines: int = 20) -> list[str]:
    target = pane_id or session_name
    if not target:
        return []
    result = run_command(["tmux", "capture-pane", "-p", "-S", f"-{max_lines}", "-t", target])
    if result.returncode != 0:
        return []
    return [line.rstrip("\n") for line in result.stdout.splitlines() if line.strip()]


def parse_exit_code(lines: list[str]) -> int | None:
    for line in reversed(lines):
        match = EXIT_CODE_PATTERN.search(line)
        if match:
            return int(match.group(1))
    return None


def build_archived_session_name(session_name: str) -> str:
    base = SESSION_SUFFIX_PATTERN.sub("", session_name)
    return f"{base}-failed-{now_stamp()}"


def parse_iso_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def restart_cooldown_passed(status: dict[str, Any]) -> bool:
    last_attempt = parse_iso_time(str(status.get("last_restart_attempt_at", "")))
    if last_attempt is None:
        return True
    delta = datetime.now(last_attempt.tzinfo or timezone.utc) - last_attempt
    return delta.total_seconds() >= RESTART_COOLDOWN_SECONDS


def should_attempt_restart(status: dict[str, Any]) -> bool:
    if status.get("status") not in RESTARTABLE_STATUSES:
        return False
    if not status.get("auto_restart"):
        return False
    if int(status.get("restart_count", 0)) >= int(status.get("max_restarts", 0)):
        return False
    return restart_cooldown_passed(status)


def build_initial_status(config: dict[str, Any], stage_order: list[str]) -> dict[str, Any]:
    restart_command = config.get("restart_command") or f"bash {shlex.quote(str(TMUX_RESTART_SCRIPT))}"
    tmux_session = config.get("tmux_session", "")
    return {
        "task_id": config["task_id"],
        "task_name": config["task_name"],
        "watchdog_id": f"watchdog-{int(time.time())}",
        "status": "running",
        "stage": stage_order[0] if stage_order else "准备中",
        "progress_mode": "stage",
        "stage_order": stage_order,
        "stage_index": 0,
        "started_at": now_iso(),
        "last_activity_at": now_iso(),
        "last_check_at": now_iso(),
        "runtime_seconds": 0,
        "idle_seconds": 0,
        "soft_timeout_seconds": config["soft_timeout_seconds"],
        "hard_timeout_seconds": config["hard_timeout_seconds"],
        "slow": False,
        "stalled": False,
        "stopped": False,
        "completed": False,
        "failed": False,
        "suggest_restart": False,
        "suggestion": "",
        "restart_command": restart_command,
        "restart_count": 0,
        "max_restarts": int(config.get("max_restarts", 0)),
        "auto_restart": bool(config.get("auto_restart", False)),
        "last_restart_at": "",
        "last_restart_attempt_at": "",
        "last_restart_reason": "",
        "pid": config["pid"],
        "log_path": config["log_path"],
        "recent_output": [],
        "last_error": "",
        "tmux_session": tmux_session,
        "tmux_window": config.get("tmux_window", "0"),
        "tmux_pane_id": config.get("tmux_pane_id", ""),
        "tmux_pane_dead": False,
        "tmux_pane_current_command": "",
        "tmux_session_exists": bool(tmux_session),
        "meta": {
            "source": config.get("source", "custom"),
            "project": config.get("project", ""),
        },
    }


def read_launch_metadata() -> dict[str, Any]:
    return read_json(LAUNCH_FILE, {})


def sync_status_with_launch(status: dict[str, Any], launch: dict[str, Any]) -> None:
    if not launch:
        return
    status["pid"] = int(launch.get("pane_pid", launch.get("pid", status.get("pid", 0))) or 0)
    status["log_path"] = str(launch.get("log_path", status.get("log_path", "")))
    status["tmux_session"] = str(launch.get("session_name", status.get("tmux_session", "")))
    status["tmux_window"] = str(launch.get("window_index", status.get("tmux_window", "0")))
    status["tmux_pane_id"] = str(launch.get("pane_id", status.get("tmux_pane_id", "")))
    status["auto_restart"] = bool(launch.get("auto_restart", status.get("auto_restart", False)))
    status["max_restarts"] = int(launch.get("max_restarts", status.get("max_restarts", 0)))
    status["soft_timeout_seconds"] = int(launch.get("soft_timeout_seconds", status.get("soft_timeout_seconds", 0)))
    status["hard_timeout_seconds"] = int(launch.get("hard_timeout_seconds", status.get("hard_timeout_seconds", 0)))
    status["restart_command"] = f"bash {shlex.quote(str(TMUX_RESTART_SCRIPT))}"


def update_tmux_fields(status: dict[str, Any], tmux_info: dict[str, Any]) -> None:
    status["tmux_session_exists"] = tmux_info["session_exists"]
    status["tmux_pane_dead"] = tmux_info["pane_dead"]
    status["tmux_pane_current_command"] = tmux_info["pane_current_command"]
    if tmux_info["pane_id"]:
        status["tmux_pane_id"] = tmux_info["pane_id"]
    if tmux_info["window_index"]:
        status["tmux_window"] = tmux_info["window_index"]
    if tmux_info["pane_pid"]:
        status["pid"] = tmux_info["pane_pid"]


def classify_status(
    status: dict[str, Any],
    *,
    alive: bool,
    exit_code: int | None,
) -> None:
    status["slow"] = False
    status["stalled"] = False
    status["stopped"] = False
    status["completed"] = False
    status["failed"] = False
    status["suggest_restart"] = False
    status["suggestion"] = ""

    if exit_code is not None:
        if exit_code == 0:
            status["status"] = "completed"
            status["completed"] = True
            status["stage"] = "完成"
            status["suggestion"] = "任务已完成"
        else:
            status["status"] = "failed"
            status["failed"] = True
            status["suggest_restart"] = True
            status["last_error"] = f"任务退出码: {exit_code}"
            status["suggestion"] = "任务异常退出，建议确认后重启"
        return

    if status["stage"] == "完成":
        status["status"] = "completed"
        status["completed"] = True
        status["suggestion"] = "任务已完成"
        return

    if not alive:
        status["status"] = "stopped"
        status["stopped"] = True
        status["suggest_restart"] = True
        status["suggestion"] = "任务已停止，建议确认后重启"
        return

    if status["idle_seconds"] >= int(status.get("hard_timeout_seconds", 0)):
        status["status"] = "stalled"
        status["stalled"] = True
        status["suggest_restart"] = True
        status["suggestion"] = "任务长时间无输出，疑似卡住"
        return

    if status["runtime_seconds"] >= int(status.get("soft_timeout_seconds", 0)):
        status["status"] = "slow"
        status["slow"] = True
        status["suggestion"] = "任务较慢，建议继续观察"
        return

    status["status"] = "running"


def attempt_restart(status: dict[str, Any], reason: str) -> tuple[bool, str]:
    archive_session = str(status.get("tmux_session", ""))
    command = ["bash", str(TMUX_RESTART_SCRIPT), "--reason", reason]
    if archive_session:
        command.extend(["--archive-session", archive_session])

    status["last_restart_attempt_at"] = now_iso()
    result = run_command(command)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
        return False, stderr
    return True, result.stdout.strip()


def run_watchdog(config: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    write_json(PID_FILE, {"pid": os.getpid(), "started_at": now_iso()})

    stage_rules = read_json(Path(config["stage_rules"]), [])
    stage_order = [str(rule["stage"]) for rule in stage_rules]
    status = build_initial_status(config, stage_order)
    write_json(STATUS_FILE, status)
    append_event("watchdog_started", {"task_id": config["task_id"]})

    previous_lines: list[str] = []
    started_ts = time.time()
    last_activity_ts = started_ts

    while True:
        launch = read_launch_metadata()
        sync_status_with_launch(status, launch)

        tmux_info = get_tmux_pane_info(status.get("tmux_session", ""), status.get("tmux_pane_id", ""))
        update_tmux_fields(status, tmux_info)

        lines = tail_text(status.get("log_path", ""))
        if not lines:
            lines = capture_tmux_output(status.get("tmux_session", ""), status.get("tmux_pane_id", ""))

        process_is_alive = process_alive(int(status.get("pid", 0)))
        tmux_alive = tmux_info["session_exists"] and tmux_info["pane_found"] and not tmux_info["pane_dead"]
        alive = tmux_alive or process_is_alive

        status["last_check_at"] = now_iso()
        status["runtime_seconds"] = int(time.time() - started_ts)

        if lines and lines != previous_lines:
            last_activity_ts = time.time()
            status["last_activity_at"] = now_iso()
            status["recent_output"] = lines[-5:]
            next_stage = infer_stage(lines, stage_rules, status["stage"])
            if next_stage != status["stage"]:
                append_event(
                    "stage_changed",
                    {
                        "task_id": config["task_id"],
                        "from": status["stage"],
                        "to": next_stage,
                    },
                )
            status["stage"] = next_stage
            status["stage_index"] = build_stage_index(status["stage"], stage_order)
            previous_lines = lines

        status["idle_seconds"] = int(time.time() - last_activity_ts)
        exit_code = parse_exit_code(lines)
        classify_status(status, alive=alive, exit_code=exit_code)

        if should_attempt_restart(status):
            ok, detail = attempt_restart(status, status["status"])
            if ok:
                status["restart_count"] = int(status.get("restart_count", 0)) + 1
                status["last_restart_at"] = now_iso()
                status["last_restart_reason"] = status["status"]
                append_event(
                    "task_restarted",
                    {
                        "task_id": status["task_id"],
                        "reason": status["status"],
                        "detail": detail,
                        "restart_count": status["restart_count"],
                    },
                )
                launch = read_launch_metadata()
                sync_status_with_launch(status, launch)
                previous_lines = []
                started_ts = time.time()
                last_activity_ts = started_ts
                status["status"] = "running"
                status["slow"] = False
                status["stalled"] = False
                status["stopped"] = False
                status["failed"] = False
                status["completed"] = False
                status["suggest_restart"] = False
                status["suggestion"] = f"已自动拉起新 session: {status.get('tmux_session', '')}"
                status["recent_output"] = []
            else:
                status["last_error"] = detail
                status["suggestion"] = f"自动重启失败: {detail}"
                append_event(
                    "restart_failed",
                    {
                        "task_id": status["task_id"],
                        "reason": status["status"],
                        "detail": detail,
                    },
                )

        write_json(STATUS_FILE, status)
        time.sleep(int(config["poll_interval_seconds"]))


def start(args: argparse.Namespace) -> None:
    config = {
        "task_id": args.task_id,
        "task_name": args.task_name,
        "pid": args.pid,
        "log_path": args.log_path,
        "soft_timeout_seconds": args.soft_timeout,
        "hard_timeout_seconds": args.hard_timeout,
        "poll_interval_seconds": args.poll_interval,
        "restart_command": args.restart_command,
        "source": args.source,
        "project": args.project,
        "stage_rules": args.stage_rules,
        "tmux_session": args.tmux_session,
        "tmux_window": args.tmux_window,
        "tmux_pane_id": args.tmux_pane_id,
        "auto_restart": args.auto_restart,
        "max_restarts": args.max_restarts,
    }
    run_watchdog(config)


def stop(_args: argparse.Namespace) -> None:
    pid_info = read_json(PID_FILE, {})
    pid = pid_info.get("pid")
    if not pid:
        print("未找到 watchdog 进程")
        return
    os.kill(int(pid), signal.SIGTERM)
    print("已停止 watchdog")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--task-id", required=True)
    start_parser.add_argument("--task-name", required=True)
    start_parser.add_argument("--pid", type=int, required=True)
    start_parser.add_argument("--log-path", required=True)
    start_parser.add_argument("--soft-timeout", type=int, default=300)
    start_parser.add_argument("--hard-timeout", type=int, default=900)
    start_parser.add_argument("--poll-interval", type=int, default=5)
    start_parser.add_argument("--restart-command", default="")
    start_parser.add_argument("--source", default="custom")
    start_parser.add_argument("--project", default="")
    start_parser.add_argument("--tmux-session", default="")
    start_parser.add_argument("--tmux-window", default="0")
    start_parser.add_argument("--tmux-pane-id", default="")
    start_parser.add_argument("--auto-restart", action="store_true")
    start_parser.add_argument("--max-restarts", type=int, default=3)
    start_parser.add_argument(
        "--stage-rules",
        default=str(BASE_DIR / "config" / "stage-rules.json"),
    )

    stop_parser = subparsers.add_parser("stop")
    stop_parser.set_defaults(func=stop)

    args = parser.parse_args()
    if args.command == "start":
        start(args)
    else:
        stop(args)


if __name__ == "__main__":
    main()
