# Tasks - Analyze claude-hud migration layers for Codex and map to AWX

## Current Status

- Current phase: analysis documentation
- Current task: completed
- Next task: none
- Blockers: none

## Task 1
- Goal:
  - Inspect current `awx` launcher, watchdog, and HUD boundaries to identify what the repository already implements.
- Files:
  - [README.md](/Users/zhang/Desktop/agent-watchdog/README.md)
  - [docs/架构说明.md](/Users/zhang/Desktop/agent-watchdog/docs/架构说明.md)
  - [scripts/awx](/Users/zhang/Desktop/agent-watchdog/scripts/awx)
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py)
  - [scripts/status.py](/Users/zhang/Desktop/agent-watchdog/scripts/status.py)
- Verification:
  - Read the files and confirm `awx` already covers launch, lifecycle, restart, and HUD rendering.
- Notes:
  - Status: completed

## Task 2
- Goal:
  - Inspect `claude-hud` source code, not just README, and extract the actual architectural layers it depends on.
- Files:
  - `claude-hud` upstream `src/index.ts`, `src/stdin.ts`, `src/transcript.ts`, `src/render/index.ts`, `src/config.ts`, `src/config-reader.ts`, `src/git.ts`, `.claude-plugin/plugin.json`, `commands/setup.md`, `commands/configure.md`
- Verification:
  - Confirm each migration layer is tied back to source code evidence.
- Notes:
  - Status: completed
  - Network note: direct git clone and archive download both stalled, so raw GitHub source files were fetched individually instead.

## Task 3
- Goal:
  - Produce a migration checklist that combines `claude-hud` layers with current `awx` implementation status and recommends a practical migration order.
- Files:
  - [code_copilot/changes/analyze-claude-hud-codex-migration/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/spec.md)
  - [code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md)
  - [code_copilot/changes/analyze-claude-hud-codex-migration/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/log.md)
- Verification:
  - Re-read the checklist and ensure each row is tagged as implemented, partial, or missing in `awx`.
- Notes:
  - Status: completed

## Resume Checklist

- Last touched files:
  - [code_copilot/changes/analyze-claude-hud-codex-migration/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/spec.md)
  - [code_copilot/changes/analyze-claude-hud-codex-migration/tasks.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/tasks.md)
  - [code_copilot/changes/analyze-claude-hud-codex-migration/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/log.md)
  - [code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/analyze-claude-hud-codex-migration/migration-checklist.md)
- Last verification command:
  - `python3 -m unittest discover -s tests`
- Last known failing point:
  - None yet. Verification not run at document creation time.
