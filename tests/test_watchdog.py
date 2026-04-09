import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WATCHDOG_PATH = REPO_ROOT / "scripts" / "watchdog.py"


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
        }

        self.assertTrue(watchdog.should_attempt_restart(status))

        status["restart_count"] = 3
        self.assertFalse(watchdog.should_attempt_restart(status))

        status["restart_count"] = 1
        status["auto_restart"] = False
        self.assertFalse(watchdog.should_attempt_restart(status))


if __name__ == "__main__":
    unittest.main()
