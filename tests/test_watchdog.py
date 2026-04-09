import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WATCHDOG_PATH = REPO_ROOT / "scripts" / "watchdog.py"
AWX_PATH = REPO_ROOT / "scripts" / "awx"
AWW_PATH = REPO_ROOT / "scripts" / "aww"
TMUX_LAUNCH_PATH = REPO_ROOT / "scripts" / "tmux_launch.sh"
START_WATCHDOG_PATH = REPO_ROOT / "scripts" / "start_watchdog.sh"
TASK_RUNNER_PATH = REPO_ROOT / "scripts" / "tmux_task_runner.sh"


def load_watchdog_module():
    spec = importlib.util.spec_from_file_location("watchdog_module", WATCHDOG_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


watchdog = load_watchdog_module()


class WatchdogTmuxTests(unittest.TestCase):
    def test_build_archived_session_name_marks_failure_and_keeps_task(self):
        archived = watchdog.build_archived_session_name("agent-demo-task-20260409-120000")

        self.assertTrue(archived.startswith("agent-demo-task-failed-"))
        self.assertNotEqual(archived, "agent-demo-task-20260409-120000")

    def test_should_attempt_restart_only_when_auto_restart_enabled_and_under_limit(self):
        status = {
            "status": "stalled",
            "auto_restart": True,
            "restart_count": 1,
            "max_restarts": 3,
            "last_restart_reason": "",
            "destroy_unattached": False,
            "tmux_session_exists": True,
        }

        self.assertTrue(watchdog.should_attempt_restart(status))

        status["restart_count"] = 3
        self.assertFalse(watchdog.should_attempt_restart(status))

        status["restart_count"] = 1
        status["auto_restart"] = False
        self.assertFalse(watchdog.should_attempt_restart(status))

    def test_should_stop_on_client_session_end_when_destroy_unattached_session_disappears(self):
        status = {
            "destroy_unattached": True,
            "tmux_session_exists": False,
        }

        self.assertTrue(watchdog.should_stop_on_client_session_end(status))
        self.assertFalse(
            watchdog.should_attempt_restart(
                {
                    **status,
                    "status": "stopped",
                    "auto_restart": True,
                    "restart_count": 0,
                    "max_restarts": 3,
                }
            )
        )

        status["tmux_session_exists"] = True
        self.assertFalse(watchdog.should_stop_on_client_session_end(status))

        status["destroy_unattached"] = False
        status["tmux_session_exists"] = False
        self.assertFalse(watchdog.should_stop_on_client_session_end(status))


class WatchdogLauncherContractTests(unittest.TestCase):
    def test_default_poll_interval_is_one_second_across_launchers(self):
        awx_script = AWX_PATH.read_text(encoding="utf-8")
        aww_script = AWW_PATH.read_text(encoding="utf-8")
        tmux_launch_script = TMUX_LAUNCH_PATH.read_text(encoding="utf-8")
        watchdog_script = WATCHDOG_PATH.read_text(encoding="utf-8")

        self.assertIn('POLL_INTERVAL="${AWW_POLL_INTERVAL:-1}"', awx_script)
        self.assertIn('POLL_INTERVAL="${AWW_POLL_INTERVAL:-1}"', aww_script)
        self.assertIn("POLL_INTERVAL=1", tmux_launch_script)
        self.assertIn('start_parser.add_argument("--poll-interval", type=int, default=1)', watchdog_script)

    def test_start_watchdog_fully_detaches_background_processes(self):
        script = START_WATCHDOG_PATH.read_text(encoding="utf-8")

        self.assertIn("</dev/null", script)
        self.assertIn("kill -0", script)
        self.assertIn('echo "$process_name 启动失败"', script)

    def test_tmux_launch_records_tool_activity_runtime_path(self):
        script = TMUX_LAUNCH_PATH.read_text(encoding="utf-8")

        self.assertIn('TOOL_ACTIVITY_PATH=""', script)
        self.assertIn('TOOL_ACTIVITY_PATH="$SESSION_RUNTIME_DIR/', script)
        self.assertIn('"tool_activity_path": os.environ["TOOL_ACTIVITY_PATH_ENV"]', script)
        self.assertIn('"runtime_dir": os.environ["SESSION_RUNTIME_DIR_ENV"]', script)

    def test_tmux_launch_provisions_tool_activity_stream(self):
        script = TMUX_LAUNCH_PATH.read_text(encoding="utf-8")

        self.assertIn('TOOL_ACTIVITY_PATH="$SESSION_RUNTIME_DIR/tool_activity.jsonl"', script)
        self.assertIn(': > "$TOOL_ACTIVITY_PATH"', script)

    def test_tmux_launch_uses_session_specific_runtime_directory(self):
        script = TMUX_LAUNCH_PATH.read_text(encoding="utf-8")

        self.assertIn('SESSION_RUNTIME_DIR="$RUNTIME_DIR/sessions/$session_name"', script)
        self.assertIn('LOG_PATH="$SESSION_RUNTIME_DIR/', script)
        self.assertIn('TOOL_ACTIVITY_PATH="$SESSION_RUNTIME_DIR/', script)
        self.assertIn('LAUNCH_FILE="$SESSION_RUNTIME_DIR/launch.json"', script)

    def test_tmux_task_runner_waits_briefly_before_command_execution(self):
        script = TASK_RUNNER_PATH.read_text(encoding="utf-8")

        self.assertIn('TASK_RUNNER_START_DELAY="${TASK_RUNNER_START_DELAY:-0.2}"', script)
        self.assertIn('sleep "$TASK_RUNNER_START_DELAY"', script)

    def test_awx_status_right_reads_session_runtime_directory(self):
        script = AWX_PATH.read_text(encoding="utf-8")

        self.assertIn("runtime_dir", script)
        self.assertIn('status-right "#($STATUS_SCRIPT --line --runtime-dir', script)


if __name__ == "__main__":
    unittest.main()
