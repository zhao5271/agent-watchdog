import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "scripts" / "status.py"


def load_status_module():
    spec = importlib.util.spec_from_file_location("status_module", STATUS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


status_module = load_status_module()


class StatusFormattingTests(unittest.TestCase):
    def test_format_status_line_includes_core_fields(self):
        line = status_module.format_status_line(
            {
                "status": "running",
                "stage": "执行中",
                "task_name": "Codex 会话",
                "idle_seconds": 12,
                "restart_count": 1,
                "max_restarts": 3,
                "recent_output": ["latest output"],
            }
        )

        self.assertIn("运行中", line)
        self.assertIn("执行中", line)
        self.assertIn("Codex 会话", line)
        self.assertIn("12s", line)
        self.assertIn("1/3", line)
        self.assertIn("latest output", line)


if __name__ == "__main__":
    unittest.main()
