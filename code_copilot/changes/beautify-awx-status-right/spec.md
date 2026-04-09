# Beautify awx status-right bottom bar

## Background and Goal

- Business or product background:
  - `awx` currently uses `python3 scripts/status.py --line` to render a single-line tmux `status-right` summary.
  - The current line is functionally complete but visually flat. It reads like a raw field dump rather than an operator-friendly status bar.
  - The current wording also creates ambiguity in completed states because machine status `已完成` and human stage `完成` appear together with very similar meaning.
  - The operator wants the bottom bar to borrow the visual rhythm of `claude-hud`, especially segmented presentation, shorter labels, and clear separation between active-state details and end-state results.
- Target outcome:
  - Redesign the single-line `status-right` summary into a more polished, segmented, claude-hud-inspired layout.
  - Keep the line in a diagnostic-balanced style: command summary, machine status, useful progress signal, runtime, idle duration, and restart count.
  - Remove the semantic collision between `已完成` and `完成`.
  - Replace the old ASCII stage bar style with a lighter stage-position marker based on circles.
  - Make mouse-wheel behavior inside `awx` session pane-local and tmux-owned: scrolling should inspect terminal output history, not trigger Codex conversation-history paging.
- Non-goals:
  - No change to the multi-line watch HUD rendered by `python3 scripts/status.py` without `--line`.
  - No change to watchdog state production, timeout classification, restart policy, or tmux pane layout.
  - No change to runtime JSON schema unless an additive helper becomes strictly necessary, which is not expected for this change.

## Current Code Reality

- Relevant files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L255) builds the current `--line` formatter as a field list joined by `|`.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L174) already has helpers for machine-status wording, duration formatting, and stage order handling.
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L89) injects `#($STATUS_SCRIPT --line)` into tmux `status-right` and caps the width at 120 characters.
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py#L142) currently locks in the old line-format contract, including simultaneous `status` and `stage`.
- Current entry points:
  - `awx` is the maintained attached workflow that displays the single-line bottom bar.
  - `python3 scripts/status.py --line` is the source of truth for the bottom-bar content.
- Current client, UI, or consumer path:
  - tmux `status-right` is the only user-facing consumer for this change.

## Functional Changes

- Server or backend changes:
  - None. Runtime state production remains unchanged.
- Client or frontend changes:
  - Change the line formatter to use `│` as the primary visual segment separator instead of plain `|`.
  - Use command summary as the leftmost anchor when available.
  - Treat `status` as the primary state label that is always shown.
  - Show `stage` only for active or in-progress states: `running`, `slow`, and `stalled`.
  - Hide `stage` entirely for terminal states: `completed`, `failed`, and `stopped`.
  - Represent in-progress stage position with a lightweight circle marker derived from `stage_index` and `stage_order`.
  - Keep runtime, idle duration, and restart count, but format them as compact segments rather than verbose labels.
  - Prefer concise Chinese wording that is visually scannable in a narrow tmux status area.
  - Configure the `awx` tmux session so mouse wheel events always enter pane-local scroll behavior instead of being passed through to the foreground TUI application.
  - Preserve keyboard-based conversation-history navigation inside Codex; only mouse-wheel behavior changes.
- Data, cache, or async changes:
  - None.

## Visual Contract

- Recommended active-state shape:
  - `codex │ 运行中 │ 执行中 ●○○○ │ 12m │ 空闲 8s │ 重启 0/3`
- Recommended terminal-state shape:
  - `codex │ 已完成 │ 总耗时 12m │ 重启 0/3`
  - `codex │ 失败 │ 运行 12m │ 空闲 4m │ 重启 1/3`

Rules:

- Active states:
  - `status` is shown first after the command summary.
  - `stage` is followed by a circle-position marker such as `●○○○`.
  - Runtime is shown as a compact duration segment.
  - Idle duration is shown as `空闲 <duration>`.
  - Restart count is shown as `重启 a/b`.
- Terminal states:
  - Do not show `stage`.
  - Do not show the circle-position marker.
  - Use `总耗时` for `completed`.
  - Keep `运行 <duration>` for `failed` and `stopped`.
  - Keep `空闲 <duration>` only when it still helps diagnose a non-success terminal state.

## API, Data, and Integration Changes

- Request or input changes:
  - No new CLI flags or environment variables.
- Response or output changes:
  - `python3 scripts/status.py --line` changes wording, separators, and field visibility rules.
  - Completed tasks no longer render both `已完成` and `完成` in the same line.
  - The stage indicator changes from plain text-only status sequencing to a `stage + circles` presentation for active states.
  - `awx` mouse-wheel behavior changes from application-defined handling to tmux-controlled pane history scrolling.
- Database, schema, or migration changes:
  - None.
- Event, queue, or cache changes:
  - None.

## Risks and Review Points

- Backward compatibility:
  - Any downstream parser that splits on ASCII `|` would break. This is acceptable because `status-right` is an operator-facing display string, not a stable machine-readable API.
  - tmux fonts or locale rendering could make some Unicode separators or circles appear uneven; the implementation should prefer simple characters with strong terminal compatibility.
  - Applications running inside `awx` will no longer receive mouse-wheel events. This is intentional for Codex-style usage but should be scoped to the `awx` session so unrelated tmux workflows are unaffected.
- Concurrency, ordering, or transaction risk:
  - None.
- Security, auth, or privacy risk:
  - None beyond the existing command-summary visibility.
- Rollback or fallback plan:
  - Revert `format_status_line` and its tests to the previous field layout.

## Verification Strategy

- Build or compile:
  - No build step.
- Automated tests:
  - Run `python3 -m unittest discover -s tests`.
  - Update `tests/test_status.py` to lock in:
    - active-state segmented layout
    - terminal-state stage suppression
    - completed-state wording without duplicated completion semantics
    - stage-position marker rendering
  - Update launcher-contract tests so `awx` session configuration explicitly enables tmux-owned wheel scrolling.
- Manual verification path:
  - Run `awx "codex"` in tmux.
  - Confirm `status-right` uses segmented `│` separators.
  - Confirm active states show `status`, `stage`, circle marker, runtime, idle duration, and restart count.
  - Confirm completed state shows only `已完成` and does not also show `完成`.
  - Confirm terminal-state wording remains readable within the current `status-right-length` constraint.
  - Confirm mouse-wheel scrolling enters tmux history for the focused pane and no longer pages Codex conversation history.
  - Confirm up/down arrow history navigation still works inside Codex.
- Logs, metrics, or dashboards to watch:
  - None. Inspect `runtime/status.json` only if the formatter output looks inconsistent with expected stage metadata.

## Open Questions

- None blocking.
