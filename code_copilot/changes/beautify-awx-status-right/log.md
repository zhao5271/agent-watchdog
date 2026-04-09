# Log - Beautify awx status-right bottom bar

- 2026-04-09 14:28:43 +0800:
  - Created a dedicated change package for the `awx` bottom status-right redesign.
  - Confirmed scope is limited to the single-line tmux bottom bar and excludes the multi-line watch HUD.
  - Captured the product issue that `已完成` and `完成` feel semantically duplicated when rendered together.
  - Agreed on a diagnostic-balanced line layout inspired by `claude-hud`.
  - Chose a circle-based progress marker for active states and stage suppression for terminal states.
  - Extended the approved scope so `awx` mouse wheel events are owned by tmux pane scrolling rather than Codex conversation-history paging.
  - Updated `scripts/status.py` so `--line` now uses segmented `│` separators, active-state stage markers like `○●○○`, and terminal-state stage suppression.
  - Updated `scripts/awx` so `awx` sessions enable tmux mouse mode, enlarge pane history, and conditionally route wheel events to tmux pane scrolling when `@awx-wheel-scroll` is enabled.
  - Extended `tests/test_status.py` to lock in the new line-format contract and the presence of session-local wheel-scroll configuration in `awx`.
  - Ran `python3 -m unittest discover -s tests` and all 12 tests passed.
