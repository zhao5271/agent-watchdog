# Build Codex transcript parser for session snapshot

## Background and Goal

- Business or product background:
  - The repository now has a written `codex_session.json` contract, but there is still no producer that can materialize it.
  - `awx` currently depends on `recent_output` plus stage-rule inference, which is useful for liveness monitoring but too weak for structured tools, agents, and todos.
  - The next P0 step is a parser/adapter that can watch Codex session artifacts and normalize them into the snapshot contract without coupling the renderer to raw logs.
- Target outcome:
  - Define the implementation plan for a first Codex parser that writes `runtime/codex_session.json`.
  - Specify input-source priority, normalization rules, incremental parsing strategy, stale/degraded behavior, and initial test coverage.
  - Keep version 1 deliberately minimal: empty or partial structured arrays are acceptable so long as the file stays valid and cheap to poll.
- Non-goals:
  - No renderer upgrade in this change.
  - No attempt to infer unsupported fields with heuristics that are less reliable than `unknown`.
  - No changes to `watchdog.py` ownership of health state.

## Current Code Reality

- Relevant files:
  - [code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md#L1) defines the target output contract.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L1) already tails raw task output and writes bounded `recent_output`, but it does not parse structured Codex events.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L202) only knows how to consume `recent_output`, not activity widgets.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) already records `log_path`, `command`, `project`, and tmux identity, which a future parser can use as producer inputs.
  - Upstream design reference:
    - `claude-hud` [`src/transcript.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/transcript.ts)
    - `claude-hud` [`src/index.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/index.ts)
    - `claude-hud` [`src/types.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/types.ts)
- Current entry points:
  - No current parser process or parser module exists in the repository.
  - The likely future entrypoint is a new script launched alongside watchdog, or a mode added to an existing runtime supervisor.
- Current service, job, or controller path:
  - Existing state production is split between launcher and watchdog.
  - The new parser must become a third producer that reads launch metadata, consumes Codex artifacts, and writes only `codex_session.json`.
- Current client, UI, or consumer path:
  - Future primary consumer is `status.py`.
  - Secondary future consumers may include HTML dashboards or notification formatters.

## Functional Changes

- Server or backend changes:
  - Add a new parser process or script that:
    - reads `runtime/launch.json`
    - detects available Codex input sources
    - incrementally parses session activity
    - writes `runtime/codex_session.json`
  - Define parser state modes:
    - `ready`
    - `degraded`
    - `unavailable`
  - Define a strict source priority:
    - structured event source if available
    - transcript-like file if available
    - raw log-derived minimal summary fallback
- Client or frontend changes:
  - None in this change, but the parser must produce renderer-friendly short labels for tools and agents.
- Data, cache, or async changes:
  - Parser should maintain an incremental cursor or cache so it does not re-read the full artifact on every poll.
  - Parser should cap collection sizes to the limits defined in the snapshot contract.

## API, Data, and Integration Changes

- Request or input changes:
  - No new user-facing CLI arguments required for the first version.
  - Internal parser inputs:
    - `launch.json.log_path`
    - `launch.json.project`
    - future explicit transcript/event path if discovered
- Response or output changes:
  - Materialize `runtime/codex_session.json` according to schema version 1.
  - Keep the file valid even when data is partial.
- Database, schema, or migration changes:
  - No database.
  - No schema change beyond adopting the already-written `codex_session.json` contract.
- Event, queue, or cache changes:
  - Add an implementation-local parser cache or cursor file only if needed for performance.
  - Parser cache is an internal detail and must not become the consumer contract.

## Risks and Review Points

- Backward compatibility:
  - The biggest risk is overfitting the parser to one observed Codex output shape and locking the contract to a fragile internal format.
  - Another risk is leaking raw transcript text instead of normalized labels, which would make the HUD noisy and unstable.
- Concurrency, ordering, or transaction risk:
  - Parser writes will race conceptually with watchdog updates, so the parser must use atomic file replacement when writing `codex_session.json`.
  - Incremental parsing must preserve event order for tool start/end, agent lifecycle, and todo updates.
- Security, auth, or privacy risk:
  - Parser should avoid persisting full prompts, user messages, or arbitrary command output when a short normalized label is enough.
- Rollback or fallback plan:
  - If the parser proves unreliable, keep `codex_session.json` absent and let the HUD fall back to `status.json.recent_output`.

## Verification Strategy

- Build or compile:
  - No build step expected.
- Automated tests:
  - Add parser-focused unit tests with fixture inputs for:
    - empty source
    - partial source
    - tool start/end lifecycle
    - agent lifecycle
    - todo replacement/update
    - stale/unavailable source fallback
  - Continue running `python3 -m unittest discover -s tests`.
- Manual verification path:
  - Launch a Codex-managed task through `awx`.
  - Confirm parser emits a valid `runtime/codex_session.json`.
  - Confirm the file remains valid when source artifacts are missing or incomplete.
  - Confirm capped arrays and short labels are enforced.
- Logs, metrics, or dashboards to watch:
  - Inspect `runtime/codex_session.json`.
  - If a parser log is added later, keep it separate from the consumer snapshot.

## Open Questions

- Question 1:
  - Should the first implementation live as a dedicated script such as `scripts/codex_session_parser.py`, or should it be launched as a mode of `watchdog.py`?
- Question 2:
  - Is there a stable Codex artifact for todos and subagents, or should version 1 leave those arrays empty until a reliable source is confirmed?
