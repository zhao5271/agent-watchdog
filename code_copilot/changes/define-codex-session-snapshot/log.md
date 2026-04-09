# Change Log - Define Codex session snapshot contract for AWX HUD

## Decisions

- 2026-04-09 15:18 CST
  - Keep `runtime/status.json` as the watchdog health contract.
  - Introduce a separate planned file, `runtime/codex_session.json`, for structured Codex session telemetry.
  - Make the snapshot source-agnostic so later producers can be built from logs, transcript files, or another local adapter.

## Findings

- `awx` already has two useful runtime sources:
  - `launch.json` for task/tmux/project metadata
  - `status.json` for health and recent output
- Those files should not be overloaded with Codex-specific telemetry because:
  - watchdog should stay independent of Codex internals
  - renderers need to tolerate Codex telemetry being absent while health monitoring still works
- A future renderer will need merged access to three files:
  - `launch.json`
  - `status.json`
  - `codex_session.json`

## Pitfalls

- Duplicating health fields like `status`, `stage`, or `idle_seconds` into `codex_session.json` would create conflicting sources of truth.
- Storing unbounded raw transcript text would make the snapshot too expensive and too noisy for HUD polling.
- Coupling the schema to Claude field names would recreate the same migration problem later.

## Spec Drift Notes

- No implementation drift. This change is documentation-only.
