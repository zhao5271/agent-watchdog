# Reassign awx to the compact status-right workflow

## Background and Goal

- Business or product background:
  - The repository currently supports three launch modes: `aww`, `awx`, and `awxbar`.
  - The operator has decided to retire the old pane-based `awx` mode and make `awx` the primary interactive attach flow for the compact status-right HUD.
  - `awxbar` should become a deprecated compatibility alias to `awx`.
  - The single-line summary used in `tmux status-right` still carries the generic task title prefix such as `Agent 任务 | codex`, which is less useful than the command-centric summary that operators look at in practice.
- Target outcome:
  - Make `awx` use the compact status-right flow with command summary, machine status, stage, runtime, idle duration, and restart count.
  - Make `awx` default to running `codex` when no command argument is provided.
  - Make `awx` lifecycle follow the attached terminal: when the last tmux client disappears because the terminal/tab closes, the tmux session and managed command should terminate instead of continuing in the background.
  - Prevent watchdog auto-restart from reviving `awx` tasks after that attached-session shutdown path.
  - Remove the generic task-name prefix from the single-line summary so `Agent 任务` no longer occupies status-right space.
  - Keep the maintained attached flow single-line only; it must not show the watch HUD's current-detail block.
  - Update docs and tests so `aww` and the new `awx` behavior are the maintained operator paths, while `awxbar` is treated as a deprecated alias.
- Non-goals:
  - No change to watchdog classification, timeout logic, restart policy, or runtime JSON schema.
  - No need to preserve the old pane-based `awx` behavior.
  - No need to change `aww` detached workflow semantics.
  - No redesign of the multi-line watch HUD beyond what is already implemented.

## Current Code Reality

- Relevant files:
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L255) builds the `--line` summary and currently prefixes it with `task_name | command_summary`.
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L1) still implements the old pane-based HUD flow.
  - [scripts/awxbar](/Users/zhang/Desktop/agent-watchdog/scripts/awxbar#L1) currently injects `python3 scripts/status.py --line` into `tmux status-right`.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) creates tmux sessions but does not currently expose a session lifecycle option such as `destroy-unattached`.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L201) attempts restart for `stopped` sessions whenever auto-restart is enabled, without distinguishing intentional attached-session shutdown from an unexpected task stop.
  - [README.md](/Users/zhang/Desktop/agent-watchdog/README.md#L48) needs to reflect the new command mapping.
  - [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py#L1) covers the formatter but does not yet lock in the launcher alias contract.
- Current entry points:
  - `awx "command"` currently launches the compact status-right flow but the tmux session remains alive after the client disconnects.
  - `awxbar "command"` currently starts the managed task, enables tmux status-right HUD, and attaches to the session.
  - `python3 scripts/status.py --line` provides the status-right content contract.
- Current service, job, or controller path:
  - `scripts/watchdog.py` writes `runtime/status.json`.
  - `scripts/status.py` formats that status for HUD consumers.
- Current client, UI, or consumer path:
  - `awx` will become the tmux status-right consumer for the line formatter.
  - `awxbar` will become a compatibility wrapper.
  - `README.md` is the operator-facing contract for which launch mode to use.

## Functional Changes

- Server or backend changes:
  - None. Runtime status production remains unchanged.
- Client or frontend changes:
  - Change the single-line formatter to use command summary as the title anchor and drop the generic `task_name` prefix.
  - Keep the line formatter compact and single-line: status, stage, runtime, idle, and restart count remain visible.
  - Replace `awx` launcher behavior with the old `awxbar` status-right attach flow.
  - Make `awx` use `codex` by default when invoked with no command.
  - Mark `awx` sessions as client-bound so the tmux session is destroyed when the last attached client disappears.
  - Teach watchdog to skip auto-restart and exit cleanly when a client-bound session disappears because the attached workflow ended.
  - Turn `awxbar` into a thin deprecated wrapper that forwards to `awx`.
  - Do not add any current-detail rows or watch-mode-only labels to the maintained attached flow.
  - Update operator docs to recommend `aww` and `awx`, and mark `awxbar` as deprecated.
- Data, cache, or async changes:
  - None.

## API, Data, and Integration Changes

- Request or input changes:
  - No new CLI flags or environment variables.
- Response or output changes:
  - `python3 scripts/status.py --line` no longer emits `task_name | ...`.
  - `awx` status-right now starts with the command summary when present, for example `codex | 运行中 | 执行中 | ...`.
  - `awx` without arguments now runs `codex`.
  - `awxbar` forwards to `awx` and prints a deprecation hint.
  - `awx` terminal/tab closure now causes the underlying tmux session, managed command, and watchdog loop to terminate instead of lingering or auto-restarting.
- Database, schema, or migration changes:
  - None.
- Event, queue, or cache changes:
  - None.

## Risks and Review Points

- Backward compatibility:
  - Users who depended on the old pane-based `awx` layout will lose that behavior.
  - Users who depended on seeing custom `AWW_TASK_NAME` text in status-right will no longer see that prefix.
  - Docs and tests must be updated to avoid conflicting guidance during the command rename.
  - A too-broad shutdown rule could accidentally suppress real auto-restart scenarios for detached workflows, so the new session-bound lifecycle must apply only to `awx`/alias flows that opt in.
- Concurrency, ordering, or transaction risk:
  - None meaningful; this is formatter and documentation work.
- Security, auth, or privacy risk:
  - None beyond the existing visibility of command summaries in tmux status-right.
- Rollback or fallback plan:
  - Restore the previous launcher scripts and `format_status_line` title composition if operators need the old mapping or task-name visibility back.

## Verification Strategy

- Build or compile:
  - No build step.
- Automated tests:
  - Run `python3 -m unittest discover -s tests`.
  - Update `tests/test_status.py` so line-summary expectations match the new `awx` contract and lock in the launcher alias behavior.
  - Update watchdog tests to verify that client-bound session loss does not trigger auto-restart.
- Manual verification path:
  - Run `awx` and confirm it starts `codex` by default.
  - Run `awx "codex"` or another command inside tmux.
  - Confirm `status-right` shows command summary, status, stage, runtime, idle duration, and restart count.
  - Confirm `status-right` does not show `Agent 任务` and does not attempt to render any current-detail block.
  - Close the attached terminal or force the last tmux client to detach, then confirm the `awx` session disappears and watchdog does not create a replacement session.
  - Run `awxbar "codex"` and confirm it forwards to `awx` with a deprecation hint.
  - Review README usage guidance and confirm `awx` is the recommended attached path.
- Logs, metrics, or dashboards to watch:
  - Inspect `runtime/status.json` only if command summary fallback behavior looks wrong.

## Open Questions

- None blocking.
