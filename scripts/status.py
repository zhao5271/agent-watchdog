#!/usr/bin/env python3
"""终端 HUD 风格状态展示。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
import unicodedata
from pathlib import Path


BASE_DIR = Path("/Users/zhang/Desktop/agent-watchdog")


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
ESC_RE = re.compile(r"\x1b[@-Z\\-_]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

DETAIL_LINE_COUNT = 3
DETAIL_MAX_WIDTH = 44
ACTIVE_LINE_STATES = {"running", "slow", "stalled"}
TERMINAL_LINE_STATES = {"completed", "failed", "stopped"}
NOISE_KEYWORDS = (
    "working",
    "tokens used",
    "/ps to view",
    "running ·",
    "conversation|input message|user message|prompt",
)
TOOL_LABELS = {
    "read": "读取",
    "search": "搜索",
    "edit": "编辑",
    "write": "写入",
    "run": "执行",
}


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}{RESET}"


def read_json(path: Path, default: dict | list | str | int | None) -> dict | list | str | int | None:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_runtime_dir(*, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> Path:
    if runtime_dir:
        return Path(runtime_dir)
    if session_name:
        return Path(base_dir) / "runtime" / "sessions" / session_name

    for latest_launch in (Path(base_dir) / "runtime" / "launch.json", Path(base_dir) / "launch.json"):
        if latest_launch.exists():
            launch = read_json(latest_launch, {})
            latest_runtime_dir = str(launch.get("runtime_dir", "")).strip()
            if latest_runtime_dir:
                return Path(latest_runtime_dir)
    return Path(base_dir) / "runtime"


def read_status(*, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> dict:
    resolved_runtime_dir = resolve_runtime_dir(runtime_dir=runtime_dir, session_name=session_name, base_dir=base_dir)
    status_file = resolved_runtime_dir / "status.json"
    codex_session_file = resolved_runtime_dir / "codex_session.json"

    if not status_file.exists():
        status = {}
    else:
        with status_file.open("r", encoding="utf-8") as handle:
            status = json.load(handle)
    if codex_session_file.exists():
        with codex_session_file.open("r", encoding="utf-8") as handle:
            codex_session = json.load(handle)
        status["activity"] = codex_session.get("activity") or {}
        status_meta = status.get("meta") or {}
        codex_meta = codex_session.get("meta") or {}
        status["meta"] = {**codex_meta, **status_meta}
    return status


def read_launch(*, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> dict:
    resolved_runtime_dir = resolve_runtime_dir(runtime_dir=runtime_dir, session_name=session_name, base_dir=base_dir)
    launch_file = resolved_runtime_dir / "launch.json"
    if not launch_file.exists():
        return {}
    with launch_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_ansi(text: str) -> str:
    cleaned = str(text).replace("\r", "")
    cleaned = OSC_RE.sub("", cleaned)
    cleaned = ANSI_RE.sub("", cleaned)
    cleaned = ESC_RE.sub("", cleaned)
    cleaned = CONTROL_RE.sub("", cleaned)
    return cleaned.strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_noise_line(text: str) -> bool:
    lowered = text.lower()
    if not lowered:
        return True
    if all(char in "-=._|/\\<>[](){}*#~:;,'\"` " for char in lowered):
        return True
    if all(unicodedata.category(char).startswith(("P", "S")) or char.isspace() for char in text):
        return True
    return any(keyword in lowered for keyword in NOISE_KEYWORDS)


def translate_detail_line(text: str) -> str:
    if text.startswith("• Ran "):
        return f"执行命令: {text[6:].strip()}"
    if text.startswith("Ran "):
        return f"执行命令: {text[4:].strip()}"
    if text.startswith("Search ") and " in " in text:
        query, scope = text[7:].split(" in ", 1)
        return f"搜索: {query.strip()} | 范围: {scope.strip()}"
    if text.startswith("Read "):
        return f"读取文件: {text[5:].strip()}"
    if text.startswith("Open "):
        return f"打开: {text[5:].strip()}"
    if text.startswith("Update "):
        return f"更新: {text[7:].strip()}"
    if text.startswith("Edit "):
        return f"编辑: {text[5:].strip()}"
    if text.startswith("Wrote "):
        return f"写入: {text[6:].strip()}"
    if text.startswith("Error: "):
        return f"错误: {text[7:].strip()}"
    if text.startswith("Failed "):
        return f"失败: {text[7:].strip()}"
    if text.startswith("│"):
        return f"命令续行: {text[1:].strip()}"
    if text.startswith("└"):
        return f"输出: {text[1:].strip()}"
    return text


def display_width(text: str) -> int:
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return width


def truncate_display(text: str, max_width: int) -> str:
    if max_width <= 0 or display_width(text) <= max_width:
        return text

    ellipsis = "..."
    ellipsis_width = len(ellipsis)
    current = 0
    pieces: list[str] = []
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        if unicodedata.combining(char):
            pieces.append(char)
            continue
        if current + char_width > max_width - ellipsis_width:
            break
        pieces.append(char)
        current += char_width
    return "".join(pieces).rstrip() + ellipsis


def detail_max_width() -> int:
    terminal_width = shutil.get_terminal_size((80, 24)).columns
    return max(24, min(DETAIL_MAX_WIDTH, terminal_width - 4))


def normalize_detail_lines(lines: list[str], limit: int = DETAIL_LINE_COUNT) -> list[str]:
    normalized: list[str] = []
    max_width = detail_max_width()
    for raw_line in lines:
        line = normalize_whitespace(strip_ansi(str(raw_line)))
        if is_noise_line(line):
            continue
        line = translate_detail_line(line)
        line = normalize_whitespace(line)
        if is_noise_line(line):
            continue
        normalized.append(truncate_display(line, max_width))
    return normalized[-limit:]


def summarize_command(command: str) -> str:
    text = strip_ansi(command)
    if not text:
        return ""
    return Path(text.split()[0]).name


def command_summary(status: dict, *, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> str:
    meta = status.get("meta") or {}
    summary = str(meta.get("command_summary", "")).strip()
    if summary:
        return summary

    launch = read_launch(runtime_dir=runtime_dir, session_name=session_name, base_dir=base_dir)
    return summarize_command(str(launch.get("command", "")))


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


def stage_marker(stage_index: int, stage_order: list[str]) -> str:
    total = max(1, len(stage_order))
    current = min(max(stage_index, 0), total - 1)
    markers = ["○"] * total
    markers[current] = "●"
    return "".join(markers)


def recent_output_lines(status: dict, limit: int = DETAIL_LINE_COUNT) -> list[str]:
    lines = status.get("recent_output") or []
    return normalize_detail_lines([str(line) for line in lines], limit=limit)


def tool_activity_lines(status: dict, limit: int = DETAIL_LINE_COUNT) -> list[str]:
    activity = status.get("activity") or {}
    tools = activity.get("tools") or []
    normalized: list[str] = []
    max_width = detail_max_width()
    for tool in tools[-limit:]:
        tool_data = tool or {}
        tool_name = str(tool_data.get("tool_name", "")).strip()
        summary = normalize_whitespace(strip_ansi(str(tool_data.get("summary", "")).strip()))
        if not summary:
            continue
        detail = summary
        if ": " in detail:
            detail = detail.split(": ", 1)[1].strip()
        label = tool_display_label(tool_name)
        rendered = f"{label} | {detail}" if label else detail
        normalized.append(truncate_display(rendered, max_width))
    return normalized[-limit:]


def tool_display_label(tool_name: str) -> str:
    normalized = normalize_whitespace(strip_ansi(str(tool_name).strip())).lower()
    if not normalized:
        return ""
    return TOOL_LABELS.get(normalized, normalized)


def compact_tool_activity_signal(status: dict, max_width: int = 28) -> str:
    activity = status.get("activity") or {}
    tools = activity.get("tools") or []
    if not tools:
        return ""
    latest = tools[-1] or {}
    tool_name = normalize_whitespace(strip_ansi(str(latest.get("tool_name", "")).strip()))
    summary = normalize_whitespace(strip_ansi(str(latest.get("summary", "")).strip()))
    if not tool_name or not summary:
        return ""
    label = tool_display_label(tool_name)
    if not label:
        return ""

    detail = summary
    if ": " in detail:
        detail = detail.split(": ", 1)[1].strip()
    detail = truncate_display(detail, max_width)
    return f"工具 {label} {detail}".strip()


def should_show_current_detail(raw_status: str) -> bool:
    return raw_status in {"running", "slow"}


def should_show_stage_in_line(raw_status: str) -> bool:
    return raw_status in ACTIVE_LINE_STATES


def should_show_idle_in_line(raw_status: str) -> bool:
    return raw_status in ACTIVE_LINE_STATES or raw_status in {"failed", "stopped"}


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


def format_status_text(status: dict, *, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> str:
    if not status:
        return "当前没有可展示的任务状态"

    raw_status = str(status.get("status", "unknown"))
    state = styled_status(raw_status)
    task_name = status.get("task_name", "-")
    summary = command_summary(status, runtime_dir=runtime_dir, session_name=session_name, base_dir=base_dir)
    title = f"{task_name} | {summary}" if summary else task_name
    stage = status.get("stage", "-")
    runtime = format_duration(int(status.get("runtime_seconds", 0)))
    idle = format_duration(int(status.get("idle_seconds", 0)))
    progress_bar = build_bar(int(status.get("stage_index", 0)), status.get("stage_order", []))
    restart_count = int(status.get("restart_count", 0))
    max_restarts = int(status.get("max_restarts", 0))
    recent_lines = recent_output_lines(status) if should_show_current_detail(raw_status) else []

    header = f"{BOLD}[watchdog]{RESET} {title}"
    line1 = f"{header} | {state}"
    line2 = f"{DIM}阶段:{RESET} {BOLD}{stage}{RESET} [{progress_bar}]"
    line3 = f"{DIM}运行:{RESET} {runtime} | {DIM}未响应:{RESET} {idle}"
    line4 = f"{DIM}重启:{RESET} {restart_count}/{max_restarts}"
    line5 = f"{DIM}当前任务细节:{RESET}"
    detail_lines = recent_lines + ["-"] * max(0, DETAIL_LINE_COUNT - len(recent_lines))
    detail_lines = detail_lines[:DETAIL_LINE_COUNT]
    tool_lines = tool_activity_lines(status)
    sections = [line1, line2, line3, line4, line5, *detail_lines]
    if tool_lines:
        sections.extend([f"{DIM}工具活动:{RESET}", *tool_lines])
    return "\n".join(sections)


def format_status_line(status: dict, *, runtime_dir: str = "", session_name: str = "", base_dir: Path = BASE_DIR) -> str:
    if not status:
        return "watchdog: no status"

    raw_status = str(status.get("status", "unknown"))
    summary = command_summary(status, runtime_dir=runtime_dir, session_name=session_name, base_dir=base_dir)
    title = summary or str(status.get("task_name", "-"))
    state = human_status(raw_status)
    stage = status.get("stage", "-")
    idle = format_duration(int(status.get("idle_seconds", 0)))
    runtime = format_duration(int(status.get("runtime_seconds", 0)))
    restart_count = int(status.get("restart_count", 0))
    max_restarts = int(status.get("max_restarts", 0))
    stage_index = int(status.get("stage_index", 0))
    stage_order = status.get("stage_order", [])

    segments = [title, state]
    if should_show_stage_in_line(raw_status):
        segments.append(f"{stage} {stage_marker(stage_index, stage_order)}")
        segments.append(runtime)
    elif raw_status == "completed":
        segments.append(f"总耗时 {runtime}")
    else:
        segments.append(f"运行 {runtime}")

    if should_show_idle_in_line(raw_status):
        segments.append(f"空闲 {idle}")

    tool_signal = compact_tool_activity_signal(status)
    if tool_signal:
        segments.append(tool_signal)

    segments.append(f"重启 {restart_count}/{max_restarts}")
    return " │ ".join(segments)


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--line", action="store_true")
    parser.add_argument("--interval", type=int, default=2)
    parser.add_argument("--runtime-dir", default="")
    parser.add_argument("--session-name", default="")
    args = parser.parse_args()

    if args.line:
        status = read_status(runtime_dir=args.runtime_dir, session_name=args.session_name)
        print(format_status_line(status, runtime_dir=args.runtime_dir, session_name=args.session_name))
        return

    if not args.watch:
        status = read_status(runtime_dir=args.runtime_dir, session_name=args.session_name)
        print(format_status_text(status, runtime_dir=args.runtime_dir, session_name=args.session_name))
        return

    try:
        while True:
            clear_screen()
            status = read_status(runtime_dir=args.runtime_dir, session_name=args.session_name)
            print(format_status_text(status, runtime_dir=args.runtime_dir, session_name=args.session_name))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n已退出 watchdog HUD 监听。")


if __name__ == "__main__":
    main()
