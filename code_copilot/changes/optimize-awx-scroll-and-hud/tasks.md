# Tasks - Optimize awx scrolling behavior and HUD detail visibility

## Task 1
- Goal:
  - Update HUD rendering so watch mode drops refresh metadata and shows a fixed-height, filtered, Chinese-normalized current execution detail block only while the task is actively executing.
- Files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Render `python3 scripts/status.py` against representative status data and confirm the HUD includes the detail block for `running` and `slow`, while omitting historical detail for inactive statuses and still omitting refresh time, refresh interval, and exit hint.
- Notes:
  - Keep the summary fields compact, render exactly 3 detail rows, truncate long rows, filter prompt/conversation-input text, and do not support historical detail browsing in the HUD.

## Task 2
- Goal:
  - Adjust `awx` tmux behavior so the focused pane scrolls like a normal terminal and the HUD pane remains navigable without hijacking the main task pane.
- Files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - Any directly related shell helper only if the interaction fix cannot stay local to `awx`
- Verification:
  - Run `awx "codex"` or another verbose command in tmux and confirm the main pane scrolls when focused, while the HUD pane can still be browsed after focus changes.
- Notes:
  - Favor pane-local behavior over global tmux settings that could affect unrelated sessions.

## Task 3
- Goal:
  - Update tests and operator-facing docs to reflect the new HUD content contract, especially that detail rows are fixed-height, translated where HUD-owned, sanitized, and only appear for the current active task state.
- Files:
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py)
  - [README.md](/Users/zhang/Desktop/agent-watchdog/README.md)
  - Relevant docs under [docs](/Users/zhang/Desktop/agent-watchdog/docs) if wording is now stale
- Verification:
  - Run `python3 -m unittest discover -s tests`.
  - Review docs examples for removed HUD header fields and for the new pane-scrolling behavior description.
- Notes:
  - Keep this task focused on the new operator contract, not a general documentation rewrite.
