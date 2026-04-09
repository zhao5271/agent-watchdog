#!/usr/bin/env python3
"""Stream tmux pane output to the raw log and a structured tool activity stream."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SEARCH_RE = re.compile(r"^Search\s+(.+?)\s+in\s+(.+)$")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def infer_tool_event(line: str) -> tuple[str, str, str] | None:
    text = line.strip()
    if not text or text.lower() == "working":
        return None
    if text.startswith("Read "):
        target = text[5:].strip()
        return ("read", f"读取文件: {target}", target)
    if text.startswith("Open "):
        target = text[5:].strip()
        return ("read", f"打开: {target}", target)
    search_match = SEARCH_RE.match(text)
    if search_match:
        query, scope = search_match.groups()
        return ("search", f"搜索: {query.strip()} | 范围: {scope.strip()}", scope.strip())
    if text.startswith("Edit "):
        target = text[5:].strip()
        return ("edit", f"编辑: {target}", target)
    if text.startswith("Update "):
        target = text[7:].strip()
        return ("edit", f"更新: {target}", target)
    if text.startswith("Wrote "):
        target = text[6:].strip()
        return ("write", f"写入: {target}", target)
    if text.startswith("Ran "):
        target = text[4:].strip()
        return ("run", f"执行命令: {target}", target)
    if text.startswith("• Ran "):
        target = text[6:].strip()
        return ("run", f"执行命令: {target}", target)
    return None


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def stream(log_path: Path, tool_activity_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tool_activity_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as raw_log:
        for line in sys.stdin:
            raw_log.write(line)
            raw_log.flush()
            event = infer_tool_event(line)
            if event is None:
                continue
            tool_name, summary, target = event
            append_jsonl(
                tool_activity_path,
                {
                    "event": "tool.finished",
                    "timestamp": now_iso(),
                    "tool_name": tool_name,
                    "summary": summary,
                    "target": target,
                    "status": "completed",
                },
            )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", required=True)
    parser.add_argument("--tool-activity-path", required=True)
    args = parser.parse_args()

    raise SystemExit(stream(Path(args.log_path), Path(args.tool_activity_path)))


if __name__ == "__main__":
    main()
