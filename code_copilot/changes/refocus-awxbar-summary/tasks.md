# Tasks - Reassign awx to the compact status-right workflow

## Current Status

- Current phase:
  - Implementation
- Current task:
  - Bind `awx` session lifecycle to the attached client and prevent watchdog auto-restart on that shutdown path.
- Next task:
  - Run tests plus a tmux smoke check for session teardown.
- Blockers:
  - None.

## Task 1
- Goal:
  - Update the single-line formatter used by the maintained attached flow so it uses command summary instead of `task_name`, while preserving status, stage, runtime, idle duration, and restart count.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
- Notes:
  - Keep the formatter single-line and do not add watch-mode detail content.

## Task 2
- Goal:
  - Update launcher scripts and tests so `awx` becomes the maintained status-right entry point with default `codex`, and `awxbar` becomes a deprecated compatibility wrapper.
- Files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [scripts/awxbar](/Users/zhang/Desktop/agent-watchdog/scripts/awxbar)
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
- Notes:
  - Remove or replace assertions that depend on the old pane-based `awx` behavior.

## Task 3
- Goal:
  - Add client-bound `awx` session teardown so closing the attached terminal also stops the tmux session and suppresses watchdog auto-restart for that workflow.
- Files:
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py)
  - [scripts/tmux_restart.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_restart.sh)
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [tests/test_watchdog.py](/Users/zhang/Desktop/agent-watchdog/tests/test_watchdog.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Verify an `awx` tmux session is destroyed when the last client detaches.
- Notes:
  - Keep this lifecycle rule opt-in so detached `aww` mode still supports auto-restart.

## Task 4
- Goal:
  - Update operator-facing docs so `awx` documents the new “closing the terminal ends the session” lifecycle and `awxbar` remains documented as deprecated.
- Files:
  - [README.md](/Users/zhang/Desktop/agent-watchdog/README.md)
- Verification:
  - Review the usage section for consistency with the new support direction.
- Notes:
  - Keep the doc changes scoped to launch-mode guidance and the new `awx` behavior.

## Resume Checklist

- Last touched files:
  - `code_copilot/changes/refocus-awxbar-summary/spec.md`
  - `code_copilot/changes/refocus-awxbar-summary/tasks.md`
  - `scripts/status.py`
  - `scripts/awx`
  - `scripts/awxbar`
  - `tests/test_status.py`
  - `README.md`
- Last verification command:
  - `tmux show-options -g | rg 'destroy-unattached|detach-on-destroy|exit-empty'`
- Last known failing point:
  - Root cause identified: tmux keeps unattached sessions alive by default, and watchdog currently restarts `stopped` sessions without distinguishing intentional client-bound shutdown.
