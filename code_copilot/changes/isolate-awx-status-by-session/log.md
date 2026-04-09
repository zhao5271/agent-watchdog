# Change Log - Isolate AWX status by tmux session

## Decisions

- 2026-04-09 16:24 CST
  - Choose full session isolation, not just tmux bar isolation.
  - Make per-session runtime directories the new source of truth.
  - Treat any top-level runtime convenience file or index as optional helper state, not primary task state.

## Findings

- `awx` already configures `status-right` per tmux session, so the missing piece is not the tmux layer but the shared runtime file model.
- `codex_session_parser.py` already supports `--runtime-dir`, which reduces the parser-side migration cost.
- `watchdog.py` still hardcodes top-level runtime file constants and is the main single-task bottleneck.
- 2026-04-09 16:34 CST
  - Implemented per-session runtime directories under `runtime/sessions/<session_name>/`.
  - `tmux_launch.sh` now writes both a session-local `launch.json` and a top-level latest-launch pointer that includes `runtime_dir`.
  - `awx` now binds `status-right` to `status.py --line --runtime-dir <session-runtime-dir>`, so each tmux session reads its own status source.
  - `start_watchdog.sh`, `watchdog.py`, `codex_session_parser.py`, and `tmux_restart.sh` now operate against session-local runtime paths.
  - Manual parallel-session verification with two `aww` sessions showed distinct runtime directories and distinct `status.py --line --runtime-dir ...` outputs (`task-one` vs `task-two`).

## Pitfalls

- Reusing global pid files and cleanup logic will cause live sessions to interfere with each other.
- Leaving `status.py` on global default files would preserve CLI ambiguity even if tmux bars become isolated.

## Spec Drift Notes

- None yet.
- 2026-04-09 16:35 CST
  - Verification passed:
    - `python3 -m unittest tests/test_watchdog.py tests/test_status.py tests/test_codex_session_parser.py`
    - `python3 -m unittest discover -s tests`
