# Analyze claude-hud migration layers for Codex and map to AWX

## Background and Goal

- Business or product background:
  - The repository already provides an `awx` / `aww` based watchdog workflow around `tmux`, `watchdog.py`, and `status.py`, but its HUD is produced from local runtime state rather than a first-class Codex session protocol.
  - The requested analysis is not a generic “clone the UI” exercise. It must identify which architectural layers in `claude-hud` are Claude-specific, which of those layers must be replaced for Codex, and which pieces `awx` already covers well enough to reuse.
  - `claude-hud` is implemented as a Claude Code plugin with a native `statusLine` command, stdin JSON contract, transcript parsing, and guided setup/configure commands. Those assumptions do not transfer directly to Codex.
- Target outcome:
  - Produce a migration-layer checklist for bringing the useful parts of `claude-hud` over to a Codex-oriented workflow.
  - Map each layer against current `awx` capabilities and call out whether the layer is already implemented, partially implemented, or missing.
  - Preserve a clear distinction between `awx` strengths that should remain as-is and missing Codex-specific telemetry layers that still need to be built.
- Non-goals:
  - No code changes to make `awx` feature-equivalent to `claude-hud` in this change.
  - No speculative implementation of Codex parsers without first confirming Codex event or transcript sources.
  - No redesign of watchdog restart semantics, tmux lifecycle, or the existing single-task runtime model.

## Current Code Reality

- Relevant files:
  - [README.md](/Users/zhang/Desktop/agent-watchdog/README.md#L1) defines the current operator contract for `aww`, `awx`, runtime files, restart behavior, and explicit future gaps such as multi-task, HTML, and notifications.
  - [docs/架构说明.md](/Users/zhang/Desktop/agent-watchdog/docs/架构说明.md#L1) documents the current system split: watchdog as state producer, HUD as state consumer.
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx#L1) binds the attached tmux workflow and injects the compact HUD into `tmux status-right`.
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh#L1) creates managed tmux sessions and writes `runtime/launch.json`.
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py#L1) is the local state engine: process health, stage inference, restart policy, and `status.json` production.
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py#L1) renders the multi-line watch HUD and compact status-right summary.
  - External reference: `claude-hud` entrypoint [`src/index.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/index.ts), stdin contract [`src/stdin.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/stdin.ts), transcript parser [`src/transcript.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/transcript.ts), renderer [`src/render/index.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/render/index.ts), config loader [`src/config.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/config.ts), config introspection [`src/config-reader.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/config-reader.ts), git layer [`src/git.ts`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/src/git.ts), plugin manifest [`.claude-plugin/plugin.json`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/.claude-plugin/plugin.json), setup flow [`commands/setup.md`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/commands/setup.md), and configure flow [`commands/configure.md`](https://raw.githubusercontent.com/jarrodwatts/claude-hud/main/commands/configure.md).
- Current entry points:
  - `awx [command]` starts an attached tmux session and shows a compact status-right HUD.
  - `aww "command"` starts the same managed workflow without auto-attach.
  - `python3 scripts/status.py` and `python3 scripts/status.py --line` expose multi-line and compact text renderers from `runtime/status.json`.
  - `claude-hud` is invoked by Claude Code’s native `statusLine` command integration and receives live stdin JSON every refresh.
- Current service, job, or controller path:
  - `awx` relies on shell launchers plus `watchdog.py` rather than a plugin/runtime callback contract.
  - Runtime truth is split across `runtime/launch.json`, `runtime/status.json`, and `runtime/events.log`.
  - There is no Codex-specific telemetry adapter layer between a Codex session and the HUD.
- Current client, UI, or consumer path:
  - Current `awx` consumers are tmux operators.
  - Current `claude-hud` consumers are Claude Code users inside native statusline rendering.
  - `awx` already owns attachment, lifecycle, and operator ergonomics better than `claude-hud`, but it exposes much less structured session activity.

## Functional Changes

- Server or backend changes:
  - None in this change. This is a repository-analysis and planning pass.
- Client or frontend changes:
  - Add a durable migration checklist document that separates “must replace for Codex” from “already present in awx”.
  - Record a recommended implementation order so later execution work can start from missing telemetry layers instead of over-polishing the existing renderer.
- Data, cache, or async changes:
  - None in implementation.
  - Analysis conclusion: if Codex transcript/event parsing is added later, `claude-hud`’s transcript/config cache pattern is worth reusing because parsing raw activity on every HUD refresh will otherwise be too expensive.

## API, Data, and Integration Changes

- Request or input changes:
  - None in this change.
  - Analysis conclusion: Codex migration will require a new adapter contract because `claude-hud` depends on Claude Code stdin fields like `transcript_path`, `cwd`, `model`, `context_window`, `cost`, and `rate_limits`, while `awx` currently only records local launch metadata plus watchdog state.
- Response or output changes:
  - New analysis artifact: a migration checklist that classifies layers by status in `awx`.
- Database, schema, or migration changes:
  - None.
- Event, queue, or cache changes:
  - None in implementation.
  - Analysis conclusion: future Codex parity probably needs a structured event cache or normalized session snapshot file in addition to today’s `recent_output`.

## Risks and Review Points

- Backward compatibility:
  - The main risk is analytical drift: treating `claude-hud` as “just a HUD” would under-scope the work, because most of its value comes from Claude-native telemetry layers rather than ANSI formatting.
  - Another risk is over-porting Claude-specific UX such as plugin setup/configure flows without checking whether Codex exposes comparable extension points.
- Concurrency, ordering, or transaction risk:
  - None in this change.
  - Future risk: if Codex event parsing is added, ordering guarantees for tool start/end, agent completion, and todo updates will matter more than today’s simple recent-log tailing.
- Security, auth, or privacy risk:
  - No new runtime risk introduced here.
  - Future review point: `claude-hud` surfaces model usage, cost, git metadata, and transcript-derived activity. A Codex port should decide explicitly which of those are safe to render in shared tmux sessions.
- Rollback or fallback plan:
  - Remove the new analysis artifact if the migration direction changes.
  - Existing runtime behavior is untouched.

## Verification Strategy

- Build or compile:
  - No build step for analysis docs.
- Automated tests:
  - Run `python3 -m unittest discover -s tests` to confirm the repository still passes after documentation-only changes.
- Manual verification path:
  - Re-read the referenced local files to confirm each claimed `awx` capability is present.
  - Re-read the referenced upstream `claude-hud` sources to confirm each migration layer is grounded in code, not just README prose.
  - Confirm the checklist distinguishes three states: already implemented in `awx`, partially implemented, and missing.
- Logs, metrics, or dashboards to watch:
  - None.

## Open Questions

- Question 1:
  - What stable Codex-native artifact should become the equivalent of Claude Code’s stdin JSON plus transcript JSONL: CLI stdout stream, session log file, MCP event feed, or a new local adapter process?
- Question 2:
  - Should Codex migration target `tmux status-right` first, or is there a better native integration point in the Codex workflow that would make `claude-hud`-style composition unnecessary?
