# Change Log - Analyze claude-hud migration layers for Codex and map to AWX

## Decisions

- 2026-04-09 15:10 CST
  - Treat this work as a spec-driven analysis change, not an implementation change.
  - Keep the top-level question focused on migration layers, not visual mimicry.
  - Use raw upstream source files as evidence because direct `git clone` and archive download both stalled in this environment.

## Findings

- `awx` is already strong on launcher/lifecycle/runtime management:
  - `awx` / `aww` / `tmux_launch.sh` manage tmux startup, attachment, and runtime file emission.
  - `watchdog.py` owns health classification, restart throttling, and replacement-session creation.
  - `status.py` already renders both multi-line and compact HUD variants.
- `claude-hud` gets most of its value from Claude-native data contracts:
  - `src/stdin.ts` expects live Claude Code stdin JSON.
  - `src/transcript.ts` parses transcript JSONL into tools, agents, todos, session duration, and token usage.
  - `src/config-reader.ts` introspects Claude config artifacts like `CLAUDE.md`, rules, MCPs, hooks, and output style.
  - `src/render/index.ts` is downstream of that structured data; it is not the hard part by itself.
- Main migration conclusion:
  - `awx` should keep its watchdog/tmux foundation.
  - The missing P0 work is a Codex session adapter plus a structured Codex parser.
  - A direct plugin-style port from Claude to Codex would likely solve the wrong problem.

## Pitfalls

- Over-scoping the renderer and under-scoping telemetry would produce a pretty HUD with weak underlying data.
- `recent_output` is not a substitute for structured tools/agents/todos.
- Claude plugin setup/configure flows cannot be assumed to exist in Codex.

## Spec Drift Notes

- No implementation drift. The repository runtime behavior was intentionally left unchanged.
