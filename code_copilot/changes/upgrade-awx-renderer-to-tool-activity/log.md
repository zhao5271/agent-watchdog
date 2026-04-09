# Change Log - Upgrade AWX renderer to tool activity

## Decisions

- 2026-04-09 16:08 CST
  - Do not rely on raw terminal output as the primary source for tool activity.
  - Introduce a dedicated structured runtime event source and keep `codex_session.json` as the aggregated consumer-facing snapshot.
  - Limit v1 structured widgets to recent tool activity and defer agents, todos, and usage telemetry.

## Findings

- The repository already has the right ownership split:
  - launcher path owns runtime initialization
  - `watchdog.py` owns health state
  - `codex_session_parser.py` owns Codex telemetry projection
  - `status.py` owns rendering
- The missing layer is not tmux rendering but stable structured activity production.
- 2026-04-09 16:21 CST
  - `tmux pipe-pane` is the lowest-risk instrumentation point because it preserves Codex TTY behavior while still giving AWX a live output stream to normalize into structured events.
  - Added `scripts/tool_activity_wrapper.py` to tee pane output into the raw log and `runtime/tool_activity.jsonl`.
  - Upgraded `codex_session_parser.py` to prefer the structured activity stream and populate `activity.tools`.
  - Upgraded `status.py` to merge `codex_session.json` into the display model and render a `工具活动` block when tool summaries are present.
 - 2026-04-09 16:05 CST
   - Root cause of the failed manual verification: `start_watchdog.sh` deleted `runtime/tool_activity.jsonl` during startup, racing with the newly started `tmux pipe-pane` wrapper.
   - Fixed the race by leaving activity stream initialization to `tmux_launch.sh`, which already truncates and provisions the file before session execution.
   - Kept the short `tmux_task_runner.sh` startup delay so very fast commands do not emit all output before `pipe-pane` is attached.

## Pitfalls

- Directly parsing pane logs for all tool semantics will keep the feature brittle and format-dependent.
- Overloading `status.json` with Codex-specific fields would blur watchdog and telemetry responsibilities.

## Spec Drift Notes

- None yet.
- 2026-04-09 16:23 CST
  - Verification passed:
    - `python3 -m unittest tests/test_tool_activity_wrapper.py`
    - `python3 -m unittest tests/test_watchdog.py`
    - `python3 -m unittest tests/test_codex_session_parser.py`
    - `python3 -m unittest tests/test_status.py`
    - `python3 -m unittest discover -s tests`
- 2026-04-09 16:04 CST
  - Manual end-to-end verification passed with `./scripts/aww "printf 'Read ...'; sleep 3"`:
    - `runtime/tool_activity.jsonl` created with structured `read/search/edit/write/run` events
    - `runtime/codex_session.json` switched to `parser_state=ready`
    - `python3 scripts/status.py` rendered the `工具活动` block
 - 2026-04-09 16:09 CST
   - Added a compact recent tool signal to the single-line HUD so `tmux status-right` can show the latest structured tool activity without requiring the multi-line view.
   - Verification passed:
     - `python3 -m unittest tests/test_status.py`
     - `python3 -m unittest discover -s tests`
 - 2026-04-09 16:12 CST
   - Normalized known tool names into short display labels for HUD rendering:
     - `read` -> `读取`
     - `search` -> `搜索`
     - `edit` -> `编辑`
     - `write` -> `写入`
     - `run` -> `执行`
   - Verification passed:
     - `python3 -m unittest tests/test_status.py`
     - `python3 -m unittest discover -s tests`
 - 2026-04-09 16:15 CST
   - Applied normalized tool labels to the multi-line `工具活动` block so both compact and expanded HUDs now use the same short vocabulary.
   - Verification passed:
     - `python3 -m unittest tests/test_status.py`
     - `python3 -m unittest discover -s tests`
