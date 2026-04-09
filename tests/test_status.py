import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "scripts" / "status.py"
AWX_PATH = REPO_ROOT / "scripts" / "awx"
AWXBAR_PATH = REPO_ROOT / "scripts" / "awxbar"


def load_status_module():
    spec = importlib.util.spec_from_file_location("status_module", STATUS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


status_module = load_status_module()


class StatusFormattingTests(unittest.TestCase):
    def test_format_status_text_uses_simplified_hud_fields(self):
        text = status_module.format_status_text(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "runtime_seconds": 3661,
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "tmux_pane_id": "%1",
                "recent_output": ["latest output"],
                "suggestion": "请重启",
                "soft_timeout_seconds": 300,
                "hard_timeout_seconds": 900,
            }
        )

        self.assertIn("Agent 任务 | codex", text)
        self.assertIn("运行中", text)
        self.assertIn("执行中", text)
        self.assertIn("[##--]", text)
        self.assertIn("运行:", text)
        self.assertIn("1h 1m 1s", text)
        self.assertIn("未响应:", text)
        self.assertIn("12s", text)
        self.assertIn("重启:", text)
        self.assertNotIn("活跃:", text)
        self.assertNotIn("最近:", text)
        self.assertNotIn("建议:", text)
        self.assertNotIn("pane:", text)
        self.assertNotIn("300/900", text)

    def test_format_status_text_shows_latest_three_recent_output_lines(self):
        text = status_module.format_status_text(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "runtime_seconds": 90,
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "recent_output": ["line1", "line2", "line3", "line4"],
            }
        )

        self.assertIn("当前任务细节:", text)
        self.assertNotIn("line1", text)
        self.assertIn("line2", text)
        self.assertIn("line3", text)
        self.assertIn("line4", text)

    def test_format_status_text_hides_recent_output_for_inactive_status(self):
        text = status_module.format_status_text(
            {
                "status": "completed",
                "stage": "完成",
                "task_name": "Agent 任务",
                "runtime_seconds": 90,
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 3,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "recent_output": ["line2", "line3", "line4"],
            }
        )

        self.assertIn("当前任务细节:", text)
        self.assertNotIn("line2", text)
        self.assertNotIn("line3", text)
        self.assertNotIn("line4", text)
        self.assertTrue(text.endswith("\n-\n-\n-") or text.endswith("-\n-\n-"))

    def test_recent_output_lines_filters_prompt_noise_and_translates_labels(self):
        lines = status_module.recent_output_lines(
            {
                "recent_output": [
                    "\u001b[39;49m\u001b[K",
                    "Working",
                    "Search 任务细节|Task Details in scripts",
                    "conversation|input message|user message|prompt",
                    "• Ran git status --short",
                    "└ modified scripts/status.py",
                ]
            }
        )

        self.assertEqual(
            lines,
            [
                "搜索: 任务细节|Task Details | 范围: scripts",
                "执行命令: git status --short",
                "输出: modified scripts/status.py",
            ],
        )

    def test_format_status_text_keeps_detail_block_fixed_height(self):
        text = status_module.format_status_text(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "runtime_seconds": 90,
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "recent_output": ["• Ran git status --short"],
            }
        )

        detail_block = text.split("当前任务细节:\x1b[0m\n", 1)[1].splitlines()
        self.assertEqual(len(detail_block), 3)
        self.assertEqual(detail_block[0], "执行命令: git status --short")
        self.assertEqual(detail_block[1], "-")
        self.assertEqual(detail_block[2], "-")

    def test_format_status_text_renders_tool_activity_block_from_structured_snapshot(self):
        text = status_module.format_status_text(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "runtime_seconds": 90,
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "recent_output": ["• Ran git status --short"],
                "activity": {
                    "tools": [
                        {"tool_name": "read", "summary": "读取文件: scripts/status.py"},
                        {"tool_name": "search", "summary": "搜索: tool activity | 范围: scripts"},
                    ]
                },
            }
        )

        self.assertIn("工具活动:", text)
        self.assertIn("读取 | scripts/status.py", text)
        self.assertIn("搜索 | tool activity | 范围: scripts", text)

    def test_format_status_line_includes_simplified_fields(self):
        line = status_module.format_status_line(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "idle_seconds": 12,
                "runtime_seconds": 90,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
            }
        )

        self.assertIn("运行中", line)
        self.assertIn("执行中", line)
        self.assertIn("codex │ 运行中 │ 执行中 ○●○○", line)
        self.assertIn("│ 1m 30s │", line)
        self.assertIn("空闲 12s", line)
        self.assertIn("12s", line)
        self.assertIn("1/3", line)
        self.assertNotIn("latest output", line)
        self.assertNotIn("未响应", line)

    def test_format_status_line_includes_compact_tool_activity_signal_when_available(self):
        line = status_module.format_status_line(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Agent 任务",
                "idle_seconds": 12,
                "runtime_seconds": 90,
                "restart_count": 1,
                "max_restarts": 3,
                "stage_index": 1,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
                "activity": {
                    "tools": [
                        {"tool_name": "edit", "summary": "编辑: scripts/status.py"},
                        {"tool_name": "run", "summary": "执行命令: pytest tests/test_status.py"},
                    ]
                },
            }
        )

        self.assertIn("工具 执行", line)
        self.assertIn("pytest tests/test_status.py", line)

    def test_tool_display_label_normalizes_known_tool_names(self):
        self.assertEqual(status_module.tool_display_label("read"), "读取")
        self.assertEqual(status_module.tool_display_label("search"), "搜索")
        self.assertEqual(status_module.tool_display_label("edit"), "编辑")
        self.assertEqual(status_module.tool_display_label("write"), "写入")
        self.assertEqual(status_module.tool_display_label("run"), "执行")
        self.assertEqual(status_module.tool_display_label("custom"), "custom")

    def test_resolve_runtime_dir_prefers_explicit_runtime_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)

            resolved = status_module.resolve_runtime_dir(runtime_dir=str(runtime_dir))

        self.assertEqual(resolved, runtime_dir)

    def test_resolve_runtime_dir_uses_latest_launch_runtime_dir_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            runtime_dir = base_dir / "runtime"
            session_runtime = runtime_dir / "sessions" / "agent-demo"
            session_runtime.mkdir(parents=True)
            runtime_dir.mkdir(parents=True, exist_ok=True)
            (runtime_dir / "launch.json").write_text(
                json.dumps({"runtime_dir": str(session_runtime)}),
                encoding="utf-8",
            )

            resolved = status_module.resolve_runtime_dir(base_dir=base_dir)

        self.assertEqual(resolved, session_runtime)

    def test_format_status_line_hides_terminal_stage_for_completed_status(self):
        line = status_module.format_status_line(
            {
                "status": "completed",
                "stage": "完成",
                "task_name": "Agent 任务",
                "idle_seconds": 12,
                "runtime_seconds": 90,
                "restart_count": 0,
                "max_restarts": 3,
                "stage_index": 3,
                "stage_order": ["准备中", "执行中", "验证中", "完成"],
                "meta": {"command_summary": "codex"},
            }
        )

        self.assertEqual(line, "codex │ 已完成 │ 总耗时 1m 30s │ 重启 0/3")
        self.assertNotIn("完成 ○", line)
        self.assertNotIn("空闲", line)


class LauncherContractTests(unittest.TestCase):
    def test_awx_defaults_to_codex_and_uses_status_right_hud(self):
        script = AWX_PATH.read_text(encoding="utf-8")

        self.assertIn('if [[ $# -eq 0 ]]; then', script)
        self.assertIn('COMMAND="codex"', script)
        self.assertIn("--destroy-unattached on", script)
        self.assertIn("client-detached", script)
        self.assertIn("tmux_client_detached_cleanup.sh", script)
        self.assertIn('status-right "#($STATUS_SCRIPT --line --runtime-dir', script)
        self.assertIn('tmux set-option -t "$SESSION_NAME" mouse on', script)
        self.assertIn('tmux set-option -t "$SESSION_NAME" @awx-wheel-scroll on', script)
        self.assertIn('tmux bind-key -T root WheelUpPane', script)
        self.assertIn('tmux bind-key -T root WheelDownPane', script)
        self.assertNotIn("tmux split-window -h", script)

    def test_awxbar_is_deprecated_wrapper_to_awx(self):
        script = AWXBAR_PATH.read_text(encoding="utf-8")

        self.assertIn('提示：awxbar 已废弃，请改用 awx。', script)
        self.assertIn('exec "$AWX_SCRIPT" "$@"', script)
        self.assertIn('exec "$AWX_SCRIPT"', script)


if __name__ == "__main__":
    unittest.main()
