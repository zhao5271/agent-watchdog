# Codex Transcript Parser Design

## Objective

Produce `runtime/codex_session.json` from the best available Codex session source without breaking when structured sources are missing.

## Producer Shape

Recommended v1 shape:

- new script: `scripts/codex_session_parser.py`
- launched alongside watchdog from the same managed workflow
- reads `runtime/launch.json`
- writes `runtime/codex_session.json` with atomic replace semantics

Reason:

- keeps watchdog responsibilities clean
- keeps renderer read-only
- gives us a clear place for parser tests and parser-local cache logic

## Input Source Priority

### Priority 1: Structured event source

Use if Codex exposes a stable machine-readable event stream.

Can populate:

- `session`
- `model`
- `context`
- `usage`
- `activity.tools`
- `activity.agents`
- `activity.todos`

### Priority 2: Transcript-like file

Use if there is a stable session transcript or JSONL artifact.

Can populate:

- `session.last_event_at`
- partial `tools`
- partial `agents`
- partial `todos`
- maybe token totals if explicitly present

### Priority 3: Raw log fallback

Use only for:

- `updated_at`
- `source`
- `meta`
- `activity.current_summary`
- maybe `session.last_event_at`

Do not infer structured `tools`, `agents`, or `todos` from noisy TUI logs unless the pattern is explicit and tested.

## Normalization Rules

### General

- prefer normalized short labels over raw text
- preserve ordering
- keep unknown fields empty instead of guessed
- cap arrays to contract limits

### Tools

Map tool lifecycle into:

- `id`
- `kind`
- `label`
- `target`
- `status`
- `started_at`
- `ended_at`

If only a tool start is known:

- emit `status: running`

If the matching end/result event later appears:

- update the same entry to `completed` or `error`

### Agents

Map subagent lifecycle into:

- `id`
- `kind`
- `model`
- `label`
- `status`
- `started_at`
- `ended_at`

If no reliable agent source exists:

- keep `agents: []`

### Todos

Treat todos as latest-state data, not append-only history.

Rules:

- updates replace previous status for the same logical item
- if a source only emits full replacements, overwrite the in-memory todo set
- if the source is unreliable, keep `todos: []`

## Parser State Rules

- `ready`
  - source is readable
  - snapshot is current
  - parsed data is trustworthy enough for consumers
- `degraded`
  - only partial source available
  - file still valid, but some widgets should be hidden
- `unavailable`
  - no usable source
  - file may still be emitted with empty arrays and warning messages

## Freshness Strategy

Each successful write should include:

- `updated_at`
- `session.last_event_at` when known
- `meta.stale`

Producer-side rule:

- if no new data arrives but source is still reachable, rewrite only when stale state changes
- avoid high-frequency rewrites without semantic changes

## Atomic Write Strategy

Write flow:

1. build full snapshot object in memory
2. write temp file in `runtime/`
3. fsync if needed
4. rename temp file to `codex_session.json`

Reason:

- readers should never see half-written JSON

## Minimal V1 Milestone

V1 is complete when the parser can:

1. start from `launch.json`
2. emit valid `codex_session.json`
3. set `meta.parser_state`
4. populate `updated_at`
5. populate `source.inputs`
6. optionally set `activity.current_summary`
7. keep `tools/agents/todos` empty when no reliable structure exists

This is enough to unblock renderer integration without pretending full parity exists.

## Test Matrix

### Unit fixtures

- missing `launch.json`
- missing source artifact
- empty source artifact
- malformed source artifact
- single tool start event
- tool start + tool result
- agent start + completion
- todo full replacement
- stale source transition
- degraded fallback from structured source to raw log summary

### Assertions

- JSON is valid
- required top-level fields always exist
- arrays are capped
- unknown fields remain empty/null
- parser state changes correctly
- no watchdog-owned fields appear in output

## Follow-On Work

After v1 parser exists:

1. teach `status.py` to read `codex_session.json`
2. render tools/agents/todos widgets only when parser state is `ready`
3. add git/workspace metadata enrichments
4. add parser cache if transcript size makes reparse too expensive
