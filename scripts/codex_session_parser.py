#!/usr/bin/env python3
"""Generate a minimal Codex session snapshot for HUD consumers."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path("/Users/zhang/Desktop/agent-watchdog")
RUNTIME_DIR = BASE_DIR / "runtime"
LAUNCH_FILE_NAME = "launch.json"
SNAPSHOT_FILE_NAME = "codex_session.json"
TOOL_ACTIVITY_FILE_NAME = "tool_activity.jsonl"

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
ESC_RE = re.compile(r"\x1b[@-Z\\-_]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
NOISE_KEYWORDS = (
    "working",
    "tokens used",
    "/ps to view",
    "running ·",
    "conversation|input message|user message|prompt",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
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


def summarize_command(command: str) -> str:
    text = strip_ansi(command)
    if not text:
        return ""
    return Path(text.split()[0]).name


def normalize_log_line(text: str) -> str:
    line = normalize_whitespace(strip_ansi(text))
    if is_noise_line(line):
        return ""
    line = translate_detail_line(line)
    line = normalize_whitespace(line)
    if is_noise_line(line):
        return ""
    return line


def recent_summary_from_log(log_path: str) -> str:
    if not log_path:
        return ""
    path = Path(log_path)
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()
    normalized = [normalize_log_line(line.rstrip("\n")) for line in lines]
    meaningful = [line for line in normalized if line]
    return meaningful[-1] if meaningful else ""


def build_snapshot(*, updated_at: str, source_kind: str, cwd: str = "", log_path: str = "", command: str = "") -> dict[str, Any]:
    command_summary = summarize_command(command)
    project_label = Path(cwd).name if cwd else ""
    return {
        "schema_version": 1,
        "updated_at": updated_at,
        "source": {
            "kind": source_kind,
            "version": "unknown",
            "inputs": {
                "log_path": log_path,
                "tool_activity_path": "",
                "transcript_path": "",
                "cwd": cwd,
            },
        },
        "session": {
            "session_id": "",
            "session_name": "",
            "started_at": "",
            "last_event_at": "",
            "mode": "interactive",
            "model": {
                "id": "",
                "display_name": "",
                "provider": "",
            },
        },
        "context": {
            "window_size": None,
            "used_tokens": None,
            "used_percent": None,
            "remaining_percent": None,
        },
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "cache_read_tokens": None,
            "cache_write_tokens": None,
            "cost_usd": None,
        },
        "activity": {
            "current_summary": "",
            "tools": [],
            "agents": [],
            "todos": [],
        },
        "meta": {
            "cwd": cwd,
            "project_label": project_label,
            "command_summary": command_summary,
            "parser_state": "unavailable",
            "stale": True,
            "warnings": [],
        },
    }


def recent_tools_from_activity_stream(tool_activity_path: str, limit: int = 3) -> list[dict[str, str]]:
    if not tool_activity_path:
        return []
    path = Path(tool_activity_path)
    if not path.exists():
        return []

    events: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            tool_name = str(payload.get("tool_name", "")).strip()
            summary = normalize_whitespace(strip_ansi(str(payload.get("summary", "")).strip()))
            target = normalize_whitespace(strip_ansi(str(payload.get("target", "")).strip()))
            status = str(payload.get("status", "")).strip() or "completed"
            timestamp = str(payload.get("timestamp", "")).strip()
            if not tool_name or not summary:
                continue
            events.append(
                {
                    "tool_name": tool_name,
                    "summary": summary,
                    "target": target,
                    "status": status,
                    "timestamp": timestamp,
                }
            )
    return events[-limit:]


def run_once(runtime_dir: Path = RUNTIME_DIR) -> dict[str, Any]:
    runtime_dir = Path(runtime_dir)
    launch_path = runtime_dir / LAUNCH_FILE_NAME
    updated_at = now_iso()

    if not launch_path.exists():
        snapshot = build_snapshot(updated_at=updated_at, source_kind="codex_adapter")
        snapshot["meta"]["warnings"].append("未找到 launch.json，无法构建 Codex 会话快照")
        return snapshot

    launch = read_json(launch_path, {})
    log_path = str(launch.get("log_path", "") or "")
    tool_activity_path = str(launch.get("tool_activity_path", "") or runtime_dir / TOOL_ACTIVITY_FILE_NAME)
    cwd = str(launch.get("project", "") or "")
    command = str(launch.get("command", "") or "")
    snapshot = build_snapshot(
        updated_at=updated_at,
        source_kind="codex_log_parser",
        cwd=cwd,
        log_path=log_path,
        command=command,
    )
    snapshot["source"]["inputs"]["tool_activity_path"] = tool_activity_path

    tools = recent_tools_from_activity_stream(tool_activity_path)
    if tools:
        snapshot["source"]["kind"] = "codex_activity_stream"
        snapshot["activity"]["tools"] = tools
        snapshot["activity"]["current_summary"] = tools[-1]["summary"]
        snapshot["session"]["last_event_at"] = tools[-1]["timestamp"] or updated_at
        snapshot["meta"]["parser_state"] = "ready"
        snapshot["meta"]["stale"] = False
        return snapshot

    summary = recent_summary_from_log(log_path)
    if summary:
        snapshot["activity"]["current_summary"] = summary
        snapshot["session"]["last_event_at"] = updated_at
        snapshot["meta"]["parser_state"] = "degraded"
        snapshot["meta"]["stale"] = False
        snapshot["meta"]["warnings"].append("当前仅使用原始日志 fallback，尚无结构化 Codex 事件源")
        return snapshot

    snapshot["meta"]["parser_state"] = "unavailable"
    snapshot["meta"]["stale"] = True
    snapshot["meta"]["warnings"].append("未找到可解析的 Codex 活动源")
    return snapshot


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
        temp_name = handle.name
    os.replace(temp_name, path)


def write_snapshot(runtime_dir: Path = RUNTIME_DIR) -> dict[str, Any]:
    runtime_dir = Path(runtime_dir)
    snapshot = run_once(runtime_dir)
    write_json_atomic(runtime_dir / SNAPSHOT_FILE_NAME, snapshot)
    return snapshot


def watch(runtime_dir: Path = RUNTIME_DIR, interval: int = 2) -> None:
    runtime_dir = Path(runtime_dir)
    while True:
        write_snapshot(runtime_dir)
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", default=str(RUNTIME_DIR))
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=2)
    args = parser.parse_args()
    runtime_dir = Path(args.runtime_dir)
    if args.watch:
        watch(runtime_dir, interval=args.interval)
        return
    write_snapshot(runtime_dir)


if __name__ == "__main__":
    main()
