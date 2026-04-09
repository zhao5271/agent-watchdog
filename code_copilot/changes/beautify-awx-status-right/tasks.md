# Tasks - Beautify awx status-right bottom bar

## Current Status

- Current phase:
  - Verification complete
- Current task:
  - Confirm implementation and automated verification results.
- Next task:
  - Run manual `awx` tmux smoke verification for wheel scrolling and line readability when convenient.
- Blockers:
  - No automated blocker. Manual tmux behavior still needs interactive confirmation.

## Task 1
- Goal:
  - Update `scripts/status.py` line formatting so the bottom bar uses segmented `│` separators and claude-hud-inspired information rhythm.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
- Notes:
  - Keep the multi-line HUD untouched.

## Task 2
- Goal:
  - Remove the completed-state wording collision by hiding `stage` for terminal states while preserving active-state progress cues.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
- Notes:
  - Terminal states are `completed`, `failed`, and `stopped`.

## Task 3
- Goal:
  - Add the circle-based active-stage marker and update tests to lock in the new visual contract.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Manually verify `awx "codex"` inside tmux.
- Notes:
  - Prefer simple Unicode characters with stable terminal rendering.

## Task 4
- Goal:
  - Make `awx` session-local mouse wheel behavior tmux-owned so scroll always inspects pane output history instead of triggering Codex history paging.
- Files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Manually verify wheel scrolling in `awx "codex"`.
- Notes:
  - Scope the change to `awx` session options and bindings only.

## Resume Checklist

- Last touched files:
  - `code_copilot/changes/beautify-awx-status-right/spec.md`
  - `code_copilot/changes/beautify-awx-status-right/tasks.md`
  - `code_copilot/changes/beautify-awx-status-right/log.md`
  - `scripts/status.py`
  - `scripts/awx`
  - `tests/test_status.py`
- Last verification command:
  - `python3 -m unittest discover -s tests`
- Last known failing point:
  - None in automated verification. Interactive tmux wheel-scroll behavior is not yet manually rechecked in this session.
