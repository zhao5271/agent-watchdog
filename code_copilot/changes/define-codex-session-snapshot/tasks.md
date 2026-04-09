# Tasks - Define Codex session snapshot contract for AWX HUD

## Current Status

- Current phase: spec drafting
- Current task: completed
- Next task: none
- Blockers: none

## Task 1
- Goal:
  - Inspect current runtime contracts and separate watchdog-owned fields from future Codex session telemetry fields.
- Files:
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py)
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
  - [docs/状态字段说明.md](/Users/zhang/Desktop/agent-watchdog/docs/状态字段说明.md)
- Verification:
  - Confirm current runtime files already cover launch metadata and health state but not structured session activity.
- Notes:
  - Status: completed

## Task 2
- Goal:
  - Draft the new `codex_session.json` contract with schema, field provenance, freshness rules, and bounded collections.
- Files:
  - [code_copilot/changes/define-codex-session-snapshot/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/spec.md)
  - [code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md)
- Verification:
  - Confirm every field is tagged as required or optional and linked to a source/owner.
- Notes:
  - Status: completed

## Task 3
- Goal:
  - Record implementation guidance so the next execution change can build the producer without reopening schema questions.
- Files:
  - [code_copilot/changes/define-codex-session-snapshot/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/log.md)
  - [code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md)
- Verification:
  - Confirm the doc includes implementation order, merge rules, and non-goals.
- Notes:
  - Status: completed

## Resume Checklist

- Last touched files:
  - [code_copilot/changes/define-codex-session-snapshot/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/spec.md)
  - [code_copilot/changes/define-codex-session-snapshot/tasks.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/tasks.md)
  - [code_copilot/changes/define-codex-session-snapshot/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/log.md)
  - [code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md)
- Last verification command:
  - `python3 -m unittest discover -s tests`
- Last known failing point:
  - None yet. Verification pending after doc creation.
