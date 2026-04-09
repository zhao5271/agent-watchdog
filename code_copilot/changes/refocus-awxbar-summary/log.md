# Log - Reassign awx to the compact status-right workflow

- 2026-04-09:
  - Created a dedicated change package for the `awxbar` summary refocus instead of reusing prior `awx`-centric HUD changes.
  - Captured the new scope: `awx` now becomes the maintained attached flow, while `awxbar` becomes a deprecated compatibility alias.
  - Planned formatter, launcher, test, and README updates to remove the `Agent 任务` prefix from status-right while preserving the core machine-status fields.
  - Updated `scripts/status.py` so `--line` starts from command summary and no longer prefixes the generic task name when summary is available.
  - Reverse-synced the change when the launcher rename requirement was clarified: old pane-based `awx` behavior is intentionally dropped, `awx` now inherits the status-right workflow, and `awxbar` remains only as a deprecated alias.
  - Updated `scripts/awx` to use the status-right HUD flow, and default to `codex` when invoked without arguments.
  - Updated `scripts/awxbar` to print a deprecation notice and forward to `awx`.
  - Extended `tests/test_status.py` to lock in the new launcher contract.
  - Updated `README.md` so the recommended attached command is now `awx`.
  - Ran `python3 -m unittest discover -s tests` and all 10 tests passed.
  - Manually smoke-tested `awx "python3 -c 'import time; print(\"awx smoke\"); time.sleep(8)'"` in tmux and confirmed the session used a single pane with `status-right` bound to `scripts/status.py --line`.
  - Confirmed `runtime/launch.json` and `tmux show-options` matched the new contract, then cleaned up the temporary session and watchdog process.
