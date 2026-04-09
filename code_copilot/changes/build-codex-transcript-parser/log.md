# Change Log - Build Codex transcript parser for session snapshot

## Decisions

- 2026-04-09 15:27 CST
  - Keep the parser independent from `watchdog.py` in responsibility, even if later launched in the same workflow.
  - Prioritize a source-agnostic parser design over a brittle one-off implementation tied to the first observed Codex output format.
  - Accept empty `tools`, `agents`, and `todos` arrays in v1 if reliable structured sources are not yet available.
- 2026-04-09 15:34 CST
  - Implement v1 as a standalone Python script with a `run_once` path first.
  - Use raw-log fallback only for `activity.current_summary`, source metadata, and parser state.
  - Treat raw-log-only output as `degraded`, not `ready`.

## Findings

- The repository already has the consumer contract (`codex_session.json`) but no producer path.
- `watchdog.py` already proves the repo can tolerate missing runtime files and bounded polling loops.
- A usable v1 parser does not need full parity:
  - valid file
  - freshness timestamps
  - parser state
  - optional current summary
  - empty structured arrays when confidence is low
- Implementation result:
  - Added `scripts/codex_session_parser.py` with `run_once`, atomic snapshot writes, and `--watch` loop mode.
  - Added `tests/test_codex_session_parser.py` to cover missing launch metadata, raw-log fallback summary generation, snapshot writes, and launcher script wiring.
  - Updated `scripts/start_watchdog.sh` and `scripts/stop_watchdog.sh` so the parser starts and stops alongside watchdog.

## Pitfalls

- Building the parser directly into `status.py` would break the current separation between producer and consumer.
- Building the parser directly into `watchdog.py` would mix health policy with Codex-specific parsing concerns.
- Treating raw logs as authoritative structured events would overfit noise instead of semantics.

## Spec Drift Notes

- Implementation completed for the approved v1 minimal scope.
