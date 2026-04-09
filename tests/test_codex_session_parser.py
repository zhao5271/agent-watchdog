import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PARSER_PATH = REPO_ROOT / "scripts" / "codex_session_parser.py"
START_WATCHDOG_PATH = REPO_ROOT / "scripts" / "start_watchdog.sh"
STOP_WATCHDOG_PATH = REPO_ROOT / "scripts" / "stop_watchdog.sh"


def load_parser_module():
    spec = importlib.util.spec_from_file_location("codex_session_parser", PARSER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parser_module = load_parser_module()


class CodexSessionParserTests(unittest.TestCase):
    def test_run_once_returns_unavailable_snapshot_when_launch_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)

            snapshot = parser_module.run_once(runtime_dir)

        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["meta"]["parser_state"], "unavailable")
        self.assertEqual(snapshot["activity"]["tools"], [])
        self.assertEqual(snapshot["activity"]["agents"], [])
        self.assertEqual(snapshot["activity"]["todos"], [])
        self.assertTrue(snapshot["meta"]["stale"])
        self.assertIn("launch.json", " ".join(snapshot["meta"]["warnings"]))

    def test_run_once_uses_raw_log_fallback_summary_and_marks_degraded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)
            log_path = runtime_dir / "demo.log"
            log_path.write_text(
                "\n".join(
                    [
                        "\u001b[39;49m\u001b[K",
                        "Working",
                        "• Ran git status --short",
                        "conversation|input message|user message|prompt",
                        "└ modified scripts/status.py",
                    ]
                ),
                encoding="utf-8",
            )
            (runtime_dir / "launch.json").write_text(
                json.dumps(
                    {
                        "command": "codex",
                        "project": "/tmp/project",
                        "log_path": str(log_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            snapshot = parser_module.run_once(runtime_dir)

        self.assertEqual(snapshot["meta"]["parser_state"], "degraded")
        self.assertFalse(snapshot["meta"]["stale"])
        self.assertEqual(snapshot["source"]["kind"], "codex_log_parser")
        self.assertEqual(snapshot["source"]["inputs"]["log_path"], str(log_path))
        self.assertEqual(snapshot["meta"]["cwd"], "/tmp/project")
        self.assertEqual(snapshot["meta"]["command_summary"], "codex")
        self.assertEqual(snapshot["activity"]["current_summary"], "输出: modified scripts/status.py")
        self.assertEqual(snapshot["activity"]["tools"], [])
        self.assertEqual(snapshot["activity"]["agents"], [])
        self.assertEqual(snapshot["activity"]["todos"], [])

    def test_write_snapshot_creates_expected_runtime_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)
            log_path = runtime_dir / "demo.log"
            log_path.write_text("Ran pytest\n", encoding="utf-8")
            (runtime_dir / "launch.json").write_text(
                json.dumps({"command": "codex", "project": "/tmp/project", "log_path": str(log_path)}),
                encoding="utf-8",
            )

            parser_module.write_snapshot(runtime_dir)
            written = json.loads((runtime_dir / "codex_session.json").read_text(encoding="utf-8"))

        self.assertEqual(written["schema_version"], 1)
        self.assertEqual(written["meta"]["parser_state"], "degraded")
        self.assertEqual(written["activity"]["current_summary"], "执行命令: pytest")

    def test_run_once_prefers_structured_tool_activity_stream(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)
            log_path = runtime_dir / "demo.log"
            tool_path = runtime_dir / "tool_activity.jsonl"
            log_path.write_text("Ran pytest\n", encoding="utf-8")
            tool_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "event": "tool.finished",
                                "timestamp": "2026-04-09T16:10:00+08:00",
                                "tool_name": "read",
                                "summary": "读取文件: scripts/status.py",
                                "target": "scripts/status.py",
                                "status": "completed",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "event": "tool.finished",
                                "timestamp": "2026-04-09T16:10:01+08:00",
                                "tool_name": "search",
                                "summary": "搜索: Tool activity | 范围: scripts",
                                "target": "scripts",
                                "status": "completed",
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime_dir / "launch.json").write_text(
                json.dumps(
                    {
                        "command": "codex",
                        "project": "/tmp/project",
                        "log_path": str(log_path),
                        "tool_activity_path": str(tool_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            snapshot = parser_module.run_once(runtime_dir)

        self.assertEqual(snapshot["meta"]["parser_state"], "ready")
        self.assertFalse(snapshot["meta"]["stale"])
        self.assertEqual(snapshot["source"]["kind"], "codex_activity_stream")
        self.assertEqual(snapshot["source"]["inputs"]["log_path"], str(log_path))
        self.assertEqual(snapshot["source"]["inputs"]["tool_activity_path"], str(tool_path))
        self.assertEqual(snapshot["activity"]["current_summary"], "搜索: Tool activity | 范围: scripts")
        self.assertEqual(
            snapshot["activity"]["tools"],
            [
                {
                    "tool_name": "read",
                    "summary": "读取文件: scripts/status.py",
                    "target": "scripts/status.py",
                    "status": "completed",
                    "timestamp": "2026-04-09T16:10:00+08:00",
                },
                {
                    "tool_name": "search",
                    "summary": "搜索: Tool activity | 范围: scripts",
                    "target": "scripts",
                    "status": "completed",
                    "timestamp": "2026-04-09T16:10:01+08:00",
                },
            ],
        )


class CodexSessionParserLauncherTests(unittest.TestCase):
    def test_start_watchdog_clears_and_launches_codex_session_parser(self):
        script = START_WATCHDOG_PATH.read_text(encoding="utf-8")

        self.assertIn('SESSION_RUNTIME_DIR="$BASE_DIR/runtime"', script)
        self.assertIn('--runtime-dir "$SESSION_RUNTIME_DIR"', script)
        self.assertIn('$SESSION_RUNTIME_DIR/codex_session.json', script)
        self.assertIn('codex_session_parser.pid', script)
        self.assertIn('codex_session_parser.out.log', script)
        self.assertIn('codex_session_parser.err.log', script)
        self.assertIn('scripts/codex_session_parser.py', script)

    def test_stop_watchdog_stops_codex_session_parser_processes(self):
        script = STOP_WATCHDOG_PATH.read_text(encoding="utf-8")

        self.assertIn('codex_session_parser.pid', script)
        self.assertIn('codex_session_parser.py --watch', script)


if __name__ == "__main__":
    unittest.main()
