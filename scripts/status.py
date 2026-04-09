#!/usr/bin/env python3
"""终端 HUD 风格状态展示。"""

from __future__ import annotations

import argparse
import json
import re
import os
import time
from datetime import datetime
from pathlib import Path


BASE_DIR = Path("/Users/zhang/Desktop/agent-watchdog")
STATUS_FILE = BASE_DIR / "runtime" / "status.json"


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}{RESET}"


def read_status() -> dict:
    if not STATUS_FILE.exists():
        return {}
    with STATUS_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text).replace("\r", "").strip()


def format_duration(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def build_bar(stage_index: int, stage_order: list[str]) -> str:
    total = max(1, len(stage_order))
    active = min(stage_index + 1, total)
    return "#" * active + "-" * (total - active)


def human_status(raw_status: str) -> str:
    mapping = {
        "running": "运行中",
        "slow": "较慢",
        "stalled": "疑似卡住",
        "stopped": "已停止",
        "completed": "已完成",
        "failed": "失败",
    }
    return mapping.get(raw_status, raw_status)


def styled_status(raw_status: str) -> str:
    text = human_status(raw_status)
    if raw_status == "running":
        return color(text, "32")
    if raw_status == "slow":
        return color(text, "33")
    if raw_status in {"stalled", "stopped", "failed"}:
        return color(text, "31")
    if raw_status == "completed":
        return color(text, "36")
    return text


def format_status_text(status: dict) -> str:
    if not status:
        return "当前没有可展示的任务状态"

    state = styled_status(status.get("status", "unknown"))
    task_name = status.get("task_name", "-")
    stage = status.get("stage", "-")
    suggestion = status.get("suggestion") or "无"
    recent_output = status.get("recent_output") or []
    latest_output = strip_ansi(recent_output[-1]) if recent_output else "暂无输出"
    runtime = format_duration(int(status.get("runtime_seconds", 0)))
    idle = format_duration(int(status.get("idle_seconds", 0)))
    threshold = f"{status.get('soft_timeout_seconds', '-')}/{status.get('hard_timeout_seconds', '-')}s"
    progress_bar = build_bar(int(status.get("stage_index", 0)), status.get("stage_order", []))
    tmux_session = status.get("tmux_session") or "-"
    pane_id = status.get("tmux_pane_id") or "-"
    restart_count = int(status.get("restart_count", 0))
    max_restarts = int(status.get("max_restarts", 0))

    header = f"{BOLD}[watchdog]{RESET} {task_name}"
    line1 = f"{header} | {state} | {BOLD}{stage}{RESET} | 建议: {suggestion}"
    line2 = f"{DIM}运行:{RESET} {runtime} | {DIM}活跃:{RESET} {idle} 前 | {DIM}阈值:{RESET} {threshold}"
    line3 = f"{DIM}阶段:{RESET} [{progress_bar}]"
    line4 = f"{DIM}tmux:{RESET} {tmux_session} | {DIM}pane:{RESET} {pane_id} | {DIM}重启:{RESET} {restart_count}/{max_restarts}"
    line5 = f"{DIM}最近:{RESET} {latest_output}"

    lines = [line1, line2, line3, line4, line5]
    if status.get("suggest_restart"):
        lines.append(color(f"重启命令: {status.get('restart_command', '')}", "31"))
    return "\n".join(lines)


def format_status_line(status: dict) -> str:
    if not status:
        return "watchdog: no status"

    task_name = status.get("task_name", "-")
    state = human_status(status.get("status", "unknown"))
    stage = status.get("stage", "-")
    idle = format_duration(int(status.get("idle_seconds", 0)))
    restart_count = int(status.get("restart_count", 0))
    max_restarts = int(status.get("max_restarts", 0))
    recent_output = status.get("recent_output") or []
    latest_output = strip_ansi(recent_output[-1]) if recent_output else "暂无输出"
    if len(latest_output) > 40:
        latest_output = latest_output[:37] + "..."

    return (
        f"{task_name} | {state} | {stage} | idle {idle} | "
        f"重启 {restart_count}/{max_restarts} | {latest_output}"
    )


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def watch_header(interval: int) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join(
        [
            f"{BOLD}Agent Watchdog HUD{RESET}",
            f"{DIM}刷新时间:{RESET} {now} | {DIM}刷新间隔:{RESET} {interval}s | {DIM}退出:{RESET} Ctrl+C",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--line", action="store_true")
    parser.add_argument("--interval", type=int, default=2)
    args = parser.parse_args()

    if args.line:
        print(format_status_line(read_status()))
        return

    if not args.watch:
        print(format_status_text(read_status()))
        return

    try:
        while True:
            clear_screen()
            print(watch_header(args.interval))
            print(format_status_text(read_status()))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n已退出 watchdog HUD 监听。")


if __name__ == "__main__":
    main()
