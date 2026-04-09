# Define Codex session snapshot contract for AWX HUD

## Background and Goal

- Business or product background:
  - The prior migration analysis concluded that `awx` already has a working launcher, watchdog, and HUD stack, but lacks a Codex-native structured session telemetry layer.
  - Today `awx` knows process and tmux facts plus a small tail of raw output. That is enough for liveness monitoring, but not enough for `claude-hud` style widgets such as tools, agents, todos, token usage, or richer environment metadata.
  - Before implementing any Codex parser or renderer upgrades, the repository needs a written snapshot contract so data producers and HUD consumers are aligned on one stable file format.
- Target outcome:
  - Define a Codex session snapshot schema that can be produced by a future Codex adapter/parser and consumed by `status.py`.
  - Specify required fields, optional fields, provenance, refresh cadence, and failure behavior.
  - Make the new snapshot complementary to existing `runtime/launch.json` and `runtime/status.json` rather than a conflicting second truth source for watchdog health.
- Non-goals:
  - No parser implementation in this change.
  - No renderer implementation in this change.
  - No changes to watchdog classification, restart policy, or current runtime file contracts in this change.

## Current Code Reality

- Relevant files:
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L1) writes `runtime/status.json` and currently owns machine health, stage inference, and recent output.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) writes `runtime/launch.json` and already captures task command, tmux session, pane, project, and runtime parameters.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L1) only reads `status.json` and `launch.json`; it has no structured Codex activity source.
  - [docs/状态字段说明.md](/Users/zhang/Desktop/agent-watchdog/docs/状态字段说明.md#L1) documents today’s status contract, which is focused on monitoring rather than session telemetry.
  - [code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md#L1) identifies the missing P0 layer: Codex session snapshot plus transcript/event parsing.
  - Upstream references:
    - `claude-hud` [`src/stdin.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/stdin.ts)
    - `claude-hud` [`src/transcript.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/transcript.ts)
    - `claude-hud` [`src/types.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/types.ts)
- Current entry points:
  - `awx` / `aww` produce runtime launch state and start watchdog.
  - No current entry point produces structured Codex activity state.
- Current service, job, or controller path:
  - `watchdog.py` is the health-state producer.
  - Future Codex adapter/parser will be a separate producer for session telemetry.
  - `status.py` is the read-only consumer and should remain a consumer.
- Current client, UI, or consumer path:
  - tmux operators consume compact and multi-line HUD output.
  - Future consumers may include `status.py`, HTML dashboards, and notifications.

## Functional Changes

- Server or backend changes:
  - Introduce a new planned runtime artifact: `runtime/codex_session.json`.
  - Define it as the structured telemetry snapshot for Codex session details, separate from watchdog health status.
  - Keep watchdog authoritative for machine-health fields such as `status`, `stage`, `idle_seconds`, `restart_count`, and restart suggestions.
- Client or frontend changes:
  - Document how HUD consumers should merge:
    - `launch.json` for launch metadata
    - `status.json` for watchdog health
    - `codex_session.json` for Codex activity and session telemetry
  - Define safe fallback behavior when `codex_session.json` is absent, stale, or partially populated.
- Data, cache, or async changes:
  - Define refresh expectations and stale-data semantics for the new snapshot.
  - Define bounded list sizes so the snapshot can be polled cheaply by HUD consumers.

## API, Data, and Integration Changes

- Request or input changes:
  - No user-facing CLI change in this spec.
  - Future producer input may come from Codex stdout logs, transcript files, local event streams, or another adapter source. This spec must stay source-agnostic.
- Response or output changes:
  - New planned file contract: `runtime/codex_session.json`.
  - The file is additive and should not replace existing runtime files.
- Database, schema, or migration changes:
  - No database.
  - The JSON schema is new and versioned with a top-level `schema_version`.
- Event, queue, or cache changes:
  - Future producers may maintain caches, but the consumer contract is the materialized snapshot file, not parser internals.

## Risks and Review Points

- Backward compatibility:
  - The biggest risk is duplicating fields already owned by `status.json`, creating disagreement between two runtime files.
  - Another risk is freezing a schema too close to Claude Code assumptions instead of keeping it Codex-source-agnostic.
- Concurrency, ordering, or transaction risk:
  - Producers will update `codex_session.json` asynchronously relative to watchdog polling.
  - Consumers must tolerate partial absence and compare freshness timestamps before trusting activity lines.
- Security, auth, or privacy risk:
  - Session snapshots may eventually include command summaries, file paths, todo text, model names, and token usage. Those are acceptable for local operator workflows but should avoid storing full prompt bodies or sensitive transcript text by default.
- Rollback or fallback plan:
  - If the planned schema proves wrong, keep using only `status.json` and `launch.json` until a revised snapshot contract is ready.

## Verification Strategy

- Build or compile:
  - No build step for this documentation change.
- Automated tests:
  - Run `python3 -m unittest discover -s tests`.
- Manual verification path:
  - Confirm the schema keeps watchdog-owned and Codex-owned concerns separate.
  - Confirm every field has a documented purpose, source, and optionality.
  - Confirm the snapshot is small enough for frequent HUD polling.
- Logs, metrics, or dashboards to watch:
  - None for this spec-only change.

## Open Questions

- Question 1:
  - Which Codex-local artifact will be the primary producer input: log tail, transcript file, or adapter-emitted structured events?
- Question 2:
  - Should session token/cost fields be strictly cumulative, or should the snapshot also include windowed rates for renderer convenience?
