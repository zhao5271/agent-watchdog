# Isolate AWX status by tmux session

## Background and Goal

- Business or product background:
  - The current `awx` HUD attaches `status-right` per tmux session, but every session reads the same global runtime files under `runtime/`.
  - Starting a new `awx` task stops the previous watchdog and overwrites `runtime/launch.json`, `runtime/status.json`, and `runtime/codex_session.json`, so older sessions show the newest task state instead of their own.
  - The user explicitly wants multi-window `awx` usage where each tmux session shows and queries its own status.
- Target outcome:
  - Move runtime state from a single global task model to a per-session runtime model.
  - Make tmux `status-right` read the current session’s status files only.
  - Make `python3 scripts/status.py` able to read a specific session runtime explicitly and support a sensible default for manual inspection.
- Non-goals:
  - No multi-session dashboard or list UI in this change.
  - No redesign of stage inference, restart policy, or tool activity parsing semantics.
  - No attempt to keep older global runtime files as the primary source of truth.

## Current Code Reality

- Relevant files:
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L1) attaches the HUD to a tmux session with `status-right "#($STATUS_SCRIPT --line)"`, but does not pass any session-specific runtime path.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) creates tmux sessions and writes a single global [launch.json](/Users/zhang/Desktop/agent-watchdog/runtime/launch.json).
  - [scripts/start_watchdog.sh](/Users/zhang/Desktop/agent-watchdog/scripts/start_watchdog.sh#L1) stops previous watchdog processes and clears global runtime files before starting the next task.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L1) reads and writes single global files such as [status.json](/Users/zhang/Desktop/agent-watchdog/runtime/status.json), [events.log](/Users/zhang/Desktop/agent-watchdog/runtime/events.log), and [launch.json](/Users/zhang/Desktop/agent-watchdog/runtime/launch.json).
  - [scripts/codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/scripts/codex_session_parser.py#L1) already accepts `--runtime-dir`, which makes it adaptable to per-session runtime directories.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L1) reads fixed global file paths and has no session selector.
  - [tests/test_watchdog.py](/Users/zhang/Desktop/agent-watchdog/tests/test_watchdog.py), [tests/test_codex_session_parser.py](/Users/zhang/Desktop/agent-watchdog/tests/test_codex_session_parser.py), and [tests/test_status.py](/Users/zhang/Desktop/agent-watchdog/tests/test_status.py) cover the current single-runtime assumptions.
- Current entry points:
  - `awx [command]`
  - `aww "command"`
  - `python3 scripts/status.py [--line]`
  - `python3 scripts/watchdog.py start ...`
  - `python3 scripts/codex_session_parser.py --watch --runtime-dir <dir>`
- Current service, job, or controller path:
  - `tmux_launch.sh` creates a session and a single global launch record.
  - `start_watchdog.sh` starts one global watchdog and one global Codex session parser.
  - `watchdog.py` and `codex_session_parser.py` write global task state.
- Current client, UI, or consumer path:
  - tmux `status-right` is configured per session, but reads global state.
  - `status.py` is a generic CLI viewer, but only for the latest global task.

## Functional Changes

- Server or backend changes:
  - Introduce per-session runtime directories under `runtime/sessions/<session_name>/`.
  - Store each session’s `launch.json`, `status.json`, `codex_session.json`, `tool_activity.jsonl`, process pid files, and logs under its own runtime directory.
  - Pass session runtime directory information into watchdog and parser processes so they no longer share global state files.
- Client or frontend changes:
  - Update tmux `status-right` to call `status.py --line --runtime-dir <session-runtime-dir>` for the current session.
  - Update `status.py` to accept `--runtime-dir` and optionally `--session-name` for manual inspection.
- Data, cache, or async changes:
  - Keep session runtime files isolated and append-only within their own directories.
  - Optionally maintain a lightweight top-level pointer or index only for convenience, not as the primary truth source.

## API, Data, and Integration Changes

- Request or input changes:
  - `watchdog.py start` gains an explicit runtime directory input.
  - `start_watchdog.sh` and `tmux_launch.sh` pass that runtime directory through the launch chain.
  - `status.py` gains runtime selection flags for CLI use.
- Response or output changes:
  - Per-session runtime files replace the current single global files as authoritative sources.
  - `tmux status-right` output becomes session-correct instead of latest-task-global.
- Database, schema, or migration changes:
  - No database changes.
  - Filesystem layout changes from:
    - `runtime/*.json`
  - To:
    - `runtime/sessions/<session_name>/*.json`
- Event, queue, or cache changes:
  - Per-session `events.log` and `tool_activity.jsonl` stay local to the session runtime directory.
  - Parser polling stays bounded within one session runtime directory.

## Risks and Review Points

- Backward compatibility:
  - Existing operators may still expect `python3 scripts/status.py` with no arguments to show something useful.
  - Existing tests and helper scripts may assume top-level `runtime/status.json`.
- Concurrency, ordering, or transaction risk:
  - Multiple watchdog and parser processes will run concurrently for different sessions, so shared global pid files and cleanup behavior must stop interfering across sessions.
  - Cleanup logic must not delete another live session’s runtime files.
- Security, auth, or privacy risk:
  - No new external exposure, but more per-session log files will accumulate on disk.
- Rollback or fallback plan:
  - Keep the runtime layout change localized behind launcher and CLI path selection so reverting can restore global paths if needed.

## Verification Strategy

- Build or compile:
  - No separate build step.
- Automated tests:
  - Add launcher tests for per-session runtime path wiring.
  - Add watchdog/parser tests that operate against explicit runtime directories.
  - Add status renderer tests for `--runtime-dir` based selection.
  - Run `python3 -m unittest tests/test_watchdog.py`
  - Run `python3 -m unittest tests/test_codex_session_parser.py`
  - Run `python3 -m unittest tests/test_status.py`
  - Run `python3 -m unittest discover -s tests`
- Manual verification path:
  - Start two `awx` sessions in parallel and confirm each tmux session shows its own status-right content.
  - Confirm each session writes to a different `runtime/sessions/<session_name>/` directory.
  - Confirm `python3 scripts/status.py --runtime-dir <dir>` reads the correct session state.
- Logs, metrics, or dashboards to watch:
  - `runtime/sessions/<session_name>/watchdog.err.log`
  - `runtime/sessions/<session_name>/codex_session_parser.err.log`
  - `runtime/sessions/<session_name>/status.json`

## Open Questions

- Question 1:
  - What should `python3 scripts/status.py` do with no selector argument: show the most recently updated session, or require explicit `--runtime-dir` / `--session-name`?
