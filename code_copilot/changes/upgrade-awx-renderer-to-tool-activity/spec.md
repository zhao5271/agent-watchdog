# Upgrade AWX renderer to tool activity

## Background and Goal

- Business or product background:
  - The repository already has a tmux-based HUD, watchdog lifecycle management, and a minimal `codex_session.json` producer.
  - The current Codex session parser only emits a degraded `current_summary` from raw logs, which is not enough to emulate `claude-hud` style tool activity.
  - The approved direction is to avoid guessing from terminal logs and instead introduce a structured local activity event source in the launcher or wrapper path.
- Target outcome:
  - Add a stable runtime activity stream that records recent Codex tool actions in a structured format.
  - Upgrade the Codex session snapshot producer to aggregate those events into `activity.tools`.
  - Upgrade the HUD renderer to display a dedicated Tool activity section while preserving the existing status and fallback behavior.
- Non-goals:
  - No attempt to fully replicate Claude Code plugin behavior or stdin integration.
  - No implementation of `agents`, `todos`, token usage, cost, or context window widgets in this change.
  - No redesign of watchdog restart policy, tmux session ownership, or multi-task runtime behavior.

## Current Code Reality

- Relevant files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L1) launches the managed tmux workflow and attaches a compact HUD to `tmux status-right`.
  - [scripts/aww](/Users/zhang/Desktop/agent-watchdog/scripts/aww#L1) launches the same workflow without auto-attach.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) creates the tmux session, pipes pane output to a raw log, writes `runtime/launch.json`, and starts watchdog.
  - [scripts/start_watchdog.sh](/Users/zhang/Desktop/agent-watchdog/scripts/start_watchdog.sh#L1) clears stale runtime state and starts both `watchdog.py` and `codex_session_parser.py`.
  - [scripts/codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/scripts/codex_session_parser.py#L1) currently emits `runtime/codex_session.json`, but only with raw-log fallback summaries and empty structured arrays.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L1) renders the multi-line HUD and compact status-right summary from `status.json` and `launch.json`.
  - [tests/test_codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/tests/test_codex_session_parser.py#L1), [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py#L1), and [tests/test_watchdog.py](/Users/zhang/Desktop/agent-watchdog/tests/test_watchdog.py#L1) cover parser, renderer, and launcher contracts.
- Current entry points:
  - `awx [command]`
  - `aww "command"`
  - `python3 scripts/status.py`
  - `python3 scripts/codex_session_parser.py --watch --runtime-dir runtime`
- Current service, job, or controller path:
  - Launcher scripts own session startup and runtime file initialization.
  - `watchdog.py` owns health state in `runtime/status.json`.
  - `codex_session_parser.py` owns Codex telemetry state in `runtime/codex_session.json`.
- Current client, UI, or consumer path:
  - tmux operators consume the compact HUD via `status-right`.
  - terminal operators can poll the full multi-line HUD via `python3 scripts/status.py`.
  - no current consumer renders structured tool widgets because no structured tool source exists yet.

## Functional Changes

- Server or backend changes:
  - Add a structured runtime activity event file, `runtime/tool_activity.jsonl`, written by the launcher or wrapper path.
  - Add a lightweight command wrapper that records bounded tool events before or while executing the managed command.
  - Update the Codex session parser to prefer structured activity events over raw-log-only fallback.
- Client or frontend changes:
  - Add a Tool activity section to the multi-line HUD.
  - Keep the one-line compact HUD focused on current status and summary unless a compact tool signal fits cleanly.
- Data, cache, or async changes:
  - Extend `launch.json` with activity event source metadata so the parser can discover the structured stream.
  - Keep only a bounded recent tool history in `codex_session.json` to avoid expensive HUD refreshes.

## API, Data, and Integration Changes

- Request or input changes:
  - `tmux_launch.sh` will pass a tool activity log path to the launched command wrapper.
  - The wrapper will write structured events without changing the user-facing `awx` and `aww` CLI contract.
- Response or output changes:
  - `launch.json` gains the tool activity source path.
  - `codex_session.json` gains populated `activity.tools` entries when structured events exist.
  - `status.py` gains a rendered Tool activity block in the multi-line view.
- Database, schema, or migration changes:
  - No database changes.
  - The new runtime event file is append-only JSON Lines.
- Event, queue, or cache changes:
  - Event schema v1 should include:
    - `event`
    - `timestamp`
    - `tool_name`
    - `summary`
    - `target`
    - `status`
  - Supported first-pass tool types:
    - `read`
    - `search`
    - `edit`
    - `write`
    - `run`

## Risks and Review Points

- Backward compatibility:
  - Existing `awx` and `aww` commands must continue to work even when the wrapper cannot infer structured events.
  - `status.py` must tolerate missing `codex_session.json` fields and missing `tool_activity.jsonl`.
- Concurrency, ordering, or transaction risk:
  - The wrapper, parser, and watchdog run asynchronously, so event writes must be append-safe and parser reads must tolerate partially written trailing lines.
  - Bounded event history is necessary so HUD polling does not scale with total session length.
- Security, auth, or privacy risk:
  - Tool event summaries may include file paths and shell commands. The implementation should avoid storing full prompt contents or large raw payloads.
- Rollback or fallback plan:
  - If structured activity events fail, the parser should fall back to the current raw-log summary path.
  - The new wrapper can be bypassed by reverting launcher wiring without affecting watchdog state.

## Verification Strategy

- Build or compile:
  - No separate build step.
- Automated tests:
  - Add parser tests for structured event ingestion and fallback precedence.
  - Add renderer tests for Tool activity output.
  - Run `python3 -m unittest tests/test_codex_session_parser.py`
  - Run `python3 -m unittest tests/test_status.py`
  - Run `python3 -m unittest discover -s tests`
- Manual verification path:
  - Launch a managed session and confirm `launch.json`, `tool_activity.jsonl`, and `codex_session.json` are produced together.
  - Confirm the HUD shows recent tool activity when structured events are present.
  - Confirm old behavior still works when the structured event file is absent.
- Logs, metrics, or dashboards to watch:
  - `runtime/codex_session_parser.err.log`
  - `runtime/watchdog.err.log`
  - `runtime/tool_activity.jsonl`

## Open Questions

- Question 1:
  - How much structured signal can the first wrapper implementation derive reliably from a managed Codex command without requiring changes inside Codex itself?
