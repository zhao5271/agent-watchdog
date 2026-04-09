# Tasks - Upgrade AWX renderer to tool activity

## Current Status

- Current phase: completed
- Current task: completed
- Next task: none
- Blockers: none

## Task 1
- Goal:
  - Add a structured tool activity event source in the launcher path and record its location in runtime metadata.
- Files:
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [scripts/aww](/Users/zhang/Desktop/agent-watchdog/scripts/aww)
  - [scripts/start_watchdog.sh](/Users/zhang/Desktop/agent-watchdog/scripts/start_watchdog.sh)
  - [tests/test_watchdog.py](/Users/zhang/Desktop/agent-watchdog/tests/test_watchdog.py)
- Verification:
  - `python3 -m unittest tests/test_watchdog.py`
- Notes:
  - Status: completed
  - `tmux_launch.sh` now provisions `runtime/tool_activity.jsonl`, records it in `launch.json`, and routes `tmux pipe-pane` through `tool_activity_wrapper.py`.
  - `start_watchdog.sh` now clears the previous activity stream on startup.

## Task 2
- Goal:
  - Upgrade the Codex session parser to aggregate recent tool events into `activity.tools` and prefer structured data over raw-log fallback.
- Files:
  - [scripts/codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/scripts/codex_session_parser.py)
  - [tests/test_codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/tests/test_codex_session_parser.py)
- Verification:
  - `python3 -m unittest tests/test_codex_session_parser.py`
- Notes:
  - Status: completed
  - `codex_session_parser.py` now prefers structured activity streams, emits `parser_state=ready`, and falls back to degraded raw-log summaries only when the structured source is absent.

## Task 3
- Goal:
  - Render a Tool activity section in the HUD using the structured Codex session snapshot.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - `python3 -m unittest tests/test_status.py`
- Notes:
  - Status: completed
  - Added the multi-line `工具活动` block while keeping the compact HUD stable for the first rollout.

## Task 4
- Goal:
  - Add a compact recent tool signal to the single-line HUD used by `tmux status-right`.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - `python3 -m unittest tests/test_status.py`
- Notes:
  - Status: completed
  - The single-line HUD now appends a short recent tool signal when structured tool activity exists.

## Task 5
- Goal:
  - Normalize tool names into short, stable display labels for HUD output.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - `python3 -m unittest tests/test_status.py`
- Notes:
  - Status: completed
  - Keep display labels short enough for `tmux status-right`.

## Task 6
- Goal:
  - Apply normalized tool labels to the multi-line `工具活动` block for consistent scanability.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - `python3 -m unittest tests/test_status.py`
- Notes:
  - Status: completed
  - Keep the multi-line block compact and avoid duplicating overly long prose.

## Resume Checklist

- Last touched files:
  - [code_copilot/changes/upgrade-awx-renderer-to-tool-activity/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/upgrade-awx-renderer-to-tool-activity/spec.md)
  - [code_copilot/changes/upgrade-awx-renderer-to-tool-activity/tasks.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/upgrade-awx-renderer-to-tool-activity/tasks.md)
- Last verification command:
  - `python3 -m unittest tests/test_status.py`
  - `python3 -m unittest discover -s tests`
  - `python3 -m unittest tests/test_tool_activity_wrapper.py`
  - `python3 -m unittest tests/test_watchdog.py`
  - `python3 -m unittest tests/test_codex_session_parser.py`
- Last known failing point:
  - None. Targeted and full-suite tests are green.
