# Tasks - Improve awx HUD layout and information selection

## Task 1
- Goal:
  - Change `awx` tmux pane orchestration from top-bottom to left-right and size the HUD pane to about 25% width while keeping focus on the main task pane.
- Files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
- Verification:
  - Launch `awx "codex"` and confirm Codex is on the left, HUD is on the right, and the HUD occupies about one quarter of the terminal width.
- Notes:
  - Prefer tmux width-based resize behavior rather than hardcoded pane height logic.

## Task 2
- Goal:
  - Simplify HUD watch-mode formatting to the approved field set and add command-summary display in the header.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
  - Potentially [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx) or [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh) only if command-summary plumbing needs a small handoff
- Verification:
  - Run `python3 scripts/status.py` against a representative `runtime/status.json` and confirm the rendered text includes only the approved items.
  - Confirm removed items no longer appear by default.
  - Confirm the HUD shows `未响应: <duration>` instead of raw timeout parameters.
- Notes:
  - Prefer deriving command summary from existing launch metadata instead of introducing new persisted watchdog fields unless necessary.

## Task 3
- Goal:
  - Update tests and perform end-to-end verification for the new layout and HUD content contract.
- Files:
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
  - Any additional targeted test file if introduced
  - Relevant docs only if behavior examples become inaccurate
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Manually verify `awx "codex"` layout and HUD content in tmux.
- Notes:
  - Keep this task focused on proof, not speculative refactoring.
