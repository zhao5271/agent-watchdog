# Tasks - Isolate AWX status by tmux session

## Current Status

- Current phase: completed
- Current task: completed
- Next task: none
- Blockers: none

## Task 1
- Goal:
  - Create per-session runtime directories and pass them through tmux launch, watchdog startup, and parser startup.
- Files:
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
  - [scripts/start_watchdog.sh](/Users/zhang/Desktop/agent-watchdog/scripts/start_watchdog.sh)
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py)
  - [tests/test_watchdog.py](/Users/zhang/Desktop/agent-watchdog/tests/test_watchdog.py)
- Verification:
  - `python3 -m unittest tests/test_watchdog.py`
- Notes:
  - Status: completed
  - Replace single global runtime paths with explicit per-session runtime directories.

## Task 2
- Goal:
  - Make `codex_session_parser.py` and related launch contracts read and write session-local snapshot files.
- Files:
  - [scripts/codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/scripts/codex_session_parser.py)
  - [tests/test_codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/tests/test_codex_session_parser.py)
- Verification:
  - `python3 -m unittest tests/test_codex_session_parser.py`
- Notes:
  - Status: completed
  - Reuse the existing `--runtime-dir` support as the per-session entry point.

## Task 3
- Goal:
  - Make `status.py` session-aware and wire tmux `status-right` to the current session runtime directory.
- Files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - `python3 -m unittest tests/test_status.py`
- Notes:
  - Status: completed
  - Preserve a useful no-argument CLI behavior while making session-specific inspection explicit.

## Resume Checklist

- Last touched files:
  - [code_copilot/changes/isolate-awx-status-by-session/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/isolate-awx-status-by-session/spec.md)
  - [code_copilot/changes/isolate-awx-status-by-session/tasks.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/isolate-awx-status-by-session/tasks.md)
- Last verification command:
  - `python3 -m unittest tests/test_watchdog.py tests/test_status.py tests/test_codex_session_parser.py`
  - `python3 -m unittest discover -s tests`
- Last known failing point:
  - None. Session-local runtime wiring and targeted manual verification are complete.
