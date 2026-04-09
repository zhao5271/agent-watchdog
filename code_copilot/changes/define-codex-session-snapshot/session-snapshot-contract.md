# Codex Session Snapshot Contract

## Purpose

`runtime/codex_session.json` is the structured, renderer-facing snapshot for Codex session telemetry.

It is not:

- the watchdog health contract
- the tmux launch contract
- a full raw transcript cache

Its job is to expose the latest bounded, structured session view that HUD consumers can poll cheaply.

## Ownership

- `runtime/launch.json`
  - owner: launcher
  - scope: command, project, tmux identity, launch parameters
- `runtime/status.json`
  - owner: watchdog
  - scope: liveness, stage, idle/runtime, restart state, recent raw output
- `runtime/codex_session.json`
  - owner: future Codex adapter/parser
  - scope: model/session/activity/tokens/todos/tools/agents/git-ready session metadata

## Top-Level Schema

```json
{
  "schema_version": 1,
  "updated_at": "2026-04-09T15:18:00+08:00",
  "source": {
    "kind": "codex_adapter",
    "version": "unknown",
    "inputs": {
      "log_path": "/abs/path/runtime/task.log",
      "transcript_path": "",
      "cwd": "/abs/path/project"
    }
  },
  "session": {
    "session_id": "",
    "session_name": "",
    "started_at": "",
    "last_event_at": "",
    "mode": "interactive",
    "model": {
      "id": "",
      "display_name": "",
      "provider": ""
    }
  },
  "context": {
    "window_size": null,
    "used_tokens": null,
    "used_percent": null,
    "remaining_percent": null
  },
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "cache_read_tokens": null,
    "cache_write_tokens": null,
    "cost_usd": null
  },
  "activity": {
    "current_summary": "",
    "tools": [],
    "agents": [],
    "todos": []
  },
  "meta": {
    "cwd": "/abs/path/project",
    "project_label": "",
    "command_summary": "",
    "parser_state": "ready",
    "stale": false,
    "warnings": []
  }
}
```

## Field Rules

### Required top-level fields

- `schema_version`
  - integer
  - used for forward migration
- `updated_at`
  - ISO timestamp
  - when the snapshot file was last materialized
- `source.kind`
  - producer identity such as `codex_adapter`, `codex_log_parser`, or `codex_transcript_parser`
- `activity.tools`
  - always present as array, possibly empty
- `activity.agents`
  - always present as array, possibly empty
- `activity.todos`
  - always present as array, possibly empty
- `meta.parser_state`
  - one of `ready`, `degraded`, `unavailable`
- `meta.stale`
  - boolean consumer hint
- `meta.warnings`
  - array of human-readable warning strings

### Optional fields

Any model, context, token, cost, session id, or started-at field may be `null` or empty when the producer cannot infer it reliably.

Rule:

- unknown is better than guessed
- bounded summary is better than raw transcript dump

## Activity Collections

### Tools

Each item:

```json
{
  "id": "",
  "kind": "read",
  "label": "Read scripts/status.py",
  "target": "scripts/status.py",
  "status": "running",
  "started_at": "",
  "ended_at": ""
}
```

Rules:

- keep at most 20 most recent tools
- `status` is `running`, `completed`, or `error`
- `label` is renderer-ready short text
- no raw prompt bodies

### Agents

Each item:

```json
{
  "id": "",
  "kind": "worker",
  "model": "",
  "label": "worker: fix tests",
  "status": "running",
  "started_at": "",
  "ended_at": ""
}
```

Rules:

- keep at most 10 most recent agents
- `kind` should reflect Codex subagent type if known

### Todos

Each item:

```json
{
  "id": "",
  "content": "Implement parser",
  "status": "in_progress",
  "updated_at": ""
}
```

Rules:

- keep latest full todo state, not append-only history
- `status` is `pending`, `in_progress`, or `completed`
- keep at most 20 items

## Freshness Rules

- producer should update `updated_at` on every successful snapshot write
- producer should update `session.last_event_at` when it sees new Codex activity
- consumer may treat the snapshot as stale when:
  - `updated_at` is older than 15 seconds during an active session
  - `meta.parser_state != "ready"`
  - the file is missing entirely

When stale:

- HUD should hide high-confidence activity widgets
- HUD may fall back to `status.json.recent_output`
- watchdog health display must continue to work unchanged

## Merge Rules For Consumers

Consumer precedence:

1. Health and restart data from `status.json`
2. Launch/tmux/project data from `launch.json`
3. Structured session telemetry from `codex_session.json`

Do not copy these into `codex_session.json`:

- watchdog `status`
- watchdog `stage`
- watchdog `idle_seconds`
- watchdog `restart_count`
- restart command or restart suggestion

Reason:

- those are owned by watchdog, not by the Codex parser

## Recommended Implementation Order

1. Implement a producer that only writes:
   - `schema_version`
   - `updated_at`
   - `source`
   - `session.last_event_at`
   - empty `tools/agents/todos`
   - `meta`
2. Extend it with structured tools and agents
3. Add todo state
4. Add model/context/token fields only when the source is trustworthy
5. Upgrade `status.py` to consume the new file

## Non-Goals For Version 1

- no full transcript persistence
- no duplicate health state
- no unbounded history arrays
- no Claude-specific field names like `rate_limits.five_hour`
- no dependence on a single Codex transport before the producer is proven
