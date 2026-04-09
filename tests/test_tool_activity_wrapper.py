import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = REPO_ROOT / "scripts" / "tool_activity_wrapper.py"


def load_wrapper_module():
    spec = importlib.util.spec_from_file_location("tool_activity_wrapper", WRAPPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


wrapper_module = load_wrapper_module()


class ToolActivityWrapperTests(unittest.TestCase):
    def test_infer_tool_event_maps_common_codex_activity_lines(self):
        self.assertEqual(
            wrapper_module.infer_tool_event("Read scripts/status.py"),
            ("read", "读取文件: scripts/status.py", "scripts/status.py"),
        )
        self.assertEqual(
            wrapper_module.infer_tool_event("Search tool activity in scripts"),
            ("search", "搜索: tool activity | 范围: scripts", "scripts"),
        )
        self.assertEqual(
            wrapper_module.infer_tool_event("Edit scripts/status.py"),
            ("edit", "编辑: scripts/status.py", "scripts/status.py"),
        )
        self.assertEqual(
            wrapper_module.infer_tool_event("Wrote scripts/status.py"),
            ("write", "写入: scripts/status.py", "scripts/status.py"),
        )
        self.assertEqual(
            wrapper_module.infer_tool_event("Ran pytest tests/test_status.py"),
            ("run", "执行命令: pytest tests/test_status.py", "pytest tests/test_status.py"),
        )

    def test_infer_tool_event_returns_none_for_noise(self):
        self.assertIsNone(wrapper_module.infer_tool_event("Working"))
        self.assertIsNone(wrapper_module.infer_tool_event(""))


if __name__ == "__main__":
    unittest.main()
