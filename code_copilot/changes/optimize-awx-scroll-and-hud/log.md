# Log - Optimize awx scrolling behavior and HUD detail visibility

- 2026-04-09:
  - Created the change package for HUD simplification and tmux scrolling behavior fixes.
  - Captured the approved design: remove HUD refresh metadata, show the latest 3 raw output lines, and make scrolling follow the focused pane.
  - Implemented the HUD update in `scripts/status.py` by removing the watch header and adding a recent-output block capped at 3 lines.
  - Updated `scripts/awx` to enable tmux mouse support and a larger history buffer for pane-local scrolling.
  - Extended tests and README to cover the new HUD contract and expected scrolling behavior.
  - Reverse-synced the change package so HUD detail semantics are stricter: only `running` and `slow` show current task detail, while inactive statuses suppress `recent_output` and do not support history viewing.
  - Updated `scripts/status.py`, tests, and docs to prevent stale detail lines from pushing higher-priority inactive-status information upward in the HUD.
