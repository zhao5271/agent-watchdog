# Improve awx HUD layout and information selection

## Background and Goal

- Business or product background:
  - `awx` currently launches a managed task in tmux, splits a second pane for the watchdog HUD, and attaches the operator to that tmux session.
  - The current HUD is perceived as unfriendly because it shows too many low-value fields and uses a vertical split that compresses the main Codex interaction area.
- Target outcome:
  - Make `awx` use a left-right split instead of an up-down split.
  - Keep the main Codex pane on the left and place the HUD pane on the right.
  - Size the HUD pane to about 25% of the total session width.
  - Reduce the default HUD content to a compact, operator-friendly set of fields.
  - Show `task_name` together with a short execution-name summary derived from the actual command, for example `Agent 任务 | codex`.
  - Show a result-oriented unresponsive duration field instead of exposing raw timeout configuration values.
- Non-goals:
  - No change to watchdog monitoring semantics, timeout detection, restart policy, or tmux restart orchestration.
  - No change to the `awxbar` status-right mode.
  - No change to `runtime/status.json` field production unless a small additive helper field is clearly justified during implementation.

## Current Code Reality

- Relevant files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L98) creates the HUD pane with `tmux split-window -v` and then resizes it by height, which produces the current top-bottom layout.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L81) renders the full-screen HUD text and currently includes task name, machine status, stage, suggestion, runtime, idle time, timeout threshold, stage bar, tmux session, pane id, restart count, recent output, and conditional restart command.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L113) renders the single-line status format and currently includes stage, idle time, restart count, and latest output.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L120) writes `runtime/launch.json`, which already contains the original command string and session metadata.
- Current entry points:
  - `awx "command"` is the operator flow that creates the layout under discussion.
  - `python3 scripts/status.py --watch` is the HUD renderer that runs inside the HUD pane.
- Current service, job, or controller path:
  - No service or controller layers. Layout control is in shell, while HUD formatting is in Python.
- Current client, UI, or consumer path:
  - The tmux-attached terminal session is the user-facing client.

## Functional Changes

- Server or backend changes:
  - Update `awx` pane creation from a vertical split to a horizontal split so the panes appear side by side.
  - Resize the HUD pane by width so it occupies roughly 25% of the available tmux window width.
- Client or frontend changes:
  - Redesign the default HUD text to show only:
    - task name plus command summary
    - machine status
    - stage
    - stage progress bar
    - runtime
    - unresponsive duration based on current `idle_seconds`
    - restart count
  - Remove these fields from the default HUD:
    - idle time
    - tmux pane id
    - recent output
    - suggestion text
    - inline restart command prompt
  - Replace raw timeout-parameter display with a direct result label such as `未响应: 12s`.
  - Show the unresponsive duration in `running` state as well, so the operator can always see how long it has been since the last activity.
- Data, cache, or async changes:
  - No database or cache changes.
  - Runtime file compatibility should remain stable. If a command-summary helper is needed, prefer deriving it from existing command data rather than changing watchdog writers.

## API, Data, and Integration Changes

- Request or input changes:
  - No new user-facing CLI arguments are required for the first iteration.
  - Existing environment variables such as `AWX_HUD_INTERVAL` must keep working unchanged.
- Response or output changes:
  - The visual layout of the tmux session changes from top-bottom to left-right.
  - The watch-mode HUD text output changes shape and field set.
  - The single-line status output should be reviewed for consistency with the simplified field model even if no user explicitly asked for it.
- Database, schema, or migration changes:
  - None.
- Event, queue, or cache changes:
  - None.

## Risks and Review Points

- Backward compatibility:
  - Users may rely on current HUD field order or wording. This is acceptable for an operator-facing terminal UI, but the change should be documented in behavior-oriented docs if the user-facing examples become stale.
  - If line-mode output is changed, tests or downstream scripts may need updates.
- Concurrency, ordering, or transaction risk:
  - tmux resize behavior can vary with small terminal widths. The implementation should use a width-based resize that behaves predictably across common terminal sizes.
  - The HUD process still runs in its own pane; changing pane orientation must not steal focus from the main pane before attach.
- Security, auth, or privacy risk:
  - Showing a command summary must avoid dumping a long or sensitive full command into a narrow HUD by default.
  - Prefer a short executable-oriented summary, not the full raw command line.
- Rollback or fallback plan:
  - Revert `scripts/awx` pane split and resize behavior.
  - Revert `scripts/status.py` formatting changes.

## Verification Strategy

- Build or compile:
  - No build step.
- Automated tests:
  - Run `python3 -m unittest discover -s tests`.
  - Add or update tests around HUD string formatting if implementation introduces helper functions or changes line-format expectations.
- Manual verification path:
  - Run `awx "codex"` in a tmux-capable terminal.
  - Confirm the session opens with Codex on the left and the HUD on the right.
  - Confirm the HUD pane width is visually close to 25% of the window width.
  - Confirm the HUD shows the selected field set and omits pane id, recent output, suggestion text, and raw timeout thresholds.
  - Confirm the HUD shows `未响应: <duration>` in both `running` and non-running states.
  - Confirm the top line shows `task_name | command summary`, for example `Agent 任务 | codex`.
- Logs, metrics, or dashboards to watch:
  - No external dashboards.
  - Check the tmux session visually and confirm `runtime/status.json` is still readable by `scripts/status.py`.

## Open Questions

- Whether the single-line `--line` format should exactly mirror the watch HUD field set or remain a separate compact summary.
