# Optimize awx scrolling behavior and HUD detail visibility

## Background and Goal

- Business or product background:
  - `awx` currently launches a managed task in tmux, splits a right-side HUD pane, and attaches the operator to the session.
  - The current HUD still includes meta header information that takes vertical space but does not help the operator make decisions during active work.
  - During active task execution, the operator needs to see the current step detail directly in the HUD and must be able to scroll the focused tmux pane like a normal terminal, especially when output exceeds the visible viewport.
- Target outcome:
  - Remove the watch-mode header fields for refresh time, refresh interval, and exit hint from the HUD.
  - Add a compact "current task detail" section to the HUD with a fixed 3-row height that cannot push the core status fields out of view.
  - Show only task execution details while the task is actively executing; do not surface user prompt or conversation input text in this block.
  - Translate HUD-owned detail labels to Chinese while keeping fixed nouns, file paths, commands, and technical identifiers unchanged.
  - Clean terminal control sequences and TUI redraw noise before display to avoid garbled detail text.
  - Make `awx` interaction closer to a normal terminal: whichever pane is focused should handle scrolling for its own visible content.
  - Do not support browsing historical detail output inside the HUD after the task leaves active execution states, so non-running statuses cannot push stale detail lines above the current machine state.
- Non-goals:
  - No change to watchdog task classification semantics, timeout thresholds, or automatic restart policy.
  - No change to `awxbar` status-right mode.
  - No redesign of runtime JSON schemas beyond additive or presentation-safe handling that supports the HUD.

## Current Code Reality

- Relevant files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L106) renders the HUD body and currently shows only the condensed status summary.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L154) renders a watch-mode header that includes refresh time, refresh interval, and exit instructions.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L246) initializes `recent_output` in runtime status.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L395) updates `recent_output` from the latest task log lines and currently keeps up to 5 lines.
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L99) creates the right-side HUD pane and immediately attaches to the tmux session, but does not currently configure explicit pane-scrolling interaction rules.
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py#L19) only verifies the simplified summary contract and does not yet cover the planned recent-output block.
- Current entry points:
  - `awx "command"` launches the tmux session with a dedicated HUD pane.
  - `python3 scripts/status.py --watch` renders the full-screen HUD in that pane.
- Current service, job, or controller path:
  - `scripts/watchdog.py` owns runtime status production.
  - `scripts/status.py` consumes `runtime/status.json` and formats the terminal HUD.
  - `scripts/awx` owns tmux layout and user attachment behavior.
- Current client, UI, or consumer path:
  - The tmux-attached terminal session is the operator-facing client.
  - The operator currently sees the main task pane and a dedicated HUD pane, but scrolling behavior does not match normal terminal expectations.
- New root-cause finding:
  - `watchdog.py` stores recent task output directly from the task log or tmux capture in `recent_output`.
  - Codex-style TUI output is not line-oriented: the log can contain cursor movement, color changes, redraw fragments, and status spinner text.
  - `status.py` only strips a basic ANSI subset and then renders the lines directly, so TUI control noise, prompt/search text, and English tool labels can leak into the detail block.

## Functional Changes

- Server or backend changes:
  - Keep producing `recent_output` in watchdog status, but treat it as raw input for the HUD, not directly renderable text.
  - Normalize raw detail candidates in the HUD-only rendering path: strip terminal control sequences, drop redraw/status noise, and remove prompt or conversation-input lines.
- Client or frontend changes:
  - Remove the watch-mode header line that shows refresh time, refresh interval, and exit hint.
  - Keep the existing high-signal summary fields: task title, machine status, stage, stage progress bar, runtime, unresponsive duration, and restart count.
  - Add a recent-output block labeled as the current execution detail and show the latest 3 normalized execution-detail lines from `recent_output` only when status is `running` or `slow`.
  - Render exactly 3 detail rows, padding with `-` when fewer than 3 usable detail lines exist.
  - Truncate each detail row to a bounded display width so long commands or Chinese text do not wrap and change the block height.
  - Translate HUD-owned labels such as `Ran` and `Search` to Chinese, while leaving commands, paths, and technical tokens unchanged.
  - For `completed`, `failed`, `stalled`, and `stopped`, do not surface historical detail lines from `recent_output`; render an empty placeholder instead.
  - Preserve `--line` output as a compact single-line summary unless implementation needs a small consistency adjustment.
- Data, cache, or async changes:
  - No database or cache changes.
  - No new background job or queue behavior.
  - Runtime file compatibility should remain stable.

## API, Data, and Integration Changes

- Request or input changes:
  - No new CLI arguments are required.
  - Existing environment variables such as `AWX_HUD_INTERVAL` and `AWX_HUD_WIDTH_PERCENT` must keep working.
- Response or output changes:
  - `python3 scripts/status.py --watch` no longer prints the watch header above the HUD body.
  - The HUD body gains a current-task-detail section showing the latest 3 raw lines only during active execution.
  - The HUD does not support historical detail browsing for inactive statuses.
  - `awx` applies tmux pane behavior changes so the focused pane can be scrolled normally by the operator.
- Database, schema, or migration changes:
  - None.
- Event, queue, or cache changes:
  - None.

## Risks and Review Points

- Backward compatibility:
  - The watch-mode HUD text shape changes, so tests and docs that assume the old header must be updated.
  - Some operators may be used to the prior HUD staying strictly summary-only; adding current-task detail increases vertical usage and should stay capped at 3 lines.
  - Operators can no longer use the HUD to inspect stale recent output after the task leaves the active execution states.
- Concurrency, ordering, or transaction risk:
  - tmux mouse and copy-mode behavior can vary by terminal and tmux version. The implementation should favor predictable pane-local scrolling instead of broad settings that break the main task pane.
  - `recent_output` ordering must remain stable so the latest visible line actually reflects the current step.
- Security, auth, or privacy risk:
  - Showing raw output in the HUD may expose sensitive command output more prominently. This is acceptable for the local operator workflow, but the implementation should avoid accidentally expanding to long unbounded logs.
- Rollback or fallback plan:
  - Revert `scripts/status.py` watch HUD formatting to the previous summary-only layout.
  - Revert `scripts/awx` tmux interaction changes if they degrade pane scrolling or focus behavior.

## Verification Strategy

- Build or compile:
  - No build step.
- Automated tests:
  - Run `python3 -m unittest discover -s tests`.
  - Update `tests/test_status.py` to verify the watch-mode text no longer shows refresh metadata, shows the latest 3 output lines only for active execution states, and suppresses historical lines for inactive states.
  - Add or update tests for helper functions if the implementation introduces tmux-interaction command builders or output sanitizers.
- Manual verification path:
  - Run `awx "codex"` or another verbose command in a tmux-capable terminal.
  - Confirm the HUD pane no longer shows refresh time, refresh interval, or exit hint.
  - Confirm the HUD shows the latest 3 raw output lines in order while the task is actively executing.
  - Confirm the HUD stops showing historical detail lines once the task becomes `completed`, `failed`, `stalled`, or `stopped`.
  - Confirm the main task pane can scroll visible overflow content when it has focus.
  - Confirm the HUD pane can still be focused and browsed with keyboard navigation when needed, but inactive-status detail remains intentionally unavailable.
  - Confirm focus returns cleanly to the main pane and scrolling follows the focused pane instead of affecting an unrelated history view.
- Logs, metrics, or dashboards to watch:
  - Inspect `runtime/status.json` to confirm `recent_output` remains readable by `scripts/status.py`.
  - No external dashboards.

## Open Questions

- None blocking. The HUD will keep the existing producer-side `recent_output` behavior and apply the active-state restriction in the renderer.
