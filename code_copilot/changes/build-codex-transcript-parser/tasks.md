# Tasks - Build Codex transcript parser for session snapshot

## Current Status

- Current phase: implementation
- Current task: completed
- Next task: upgrade `status.py` to consume `codex_session.json`
- Blockers: none

## Task 1
- Goal:
  - Define the parser’s boundary relative to launcher, watchdog, and renderer.
- Files:
  - [code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/define-codex-session-snapshot/session-snapshot-contract.md)
  - [scripts/watchdog.py](/Users/zhang/Desktop/agent-watchdog/scripts/watchdog.py)
  - [scripts/tmux_launch.sh](/Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh)
- Verification:
  - Confirm parser owns only `codex_session.json` and does not take over watchdog health concerns.
- Notes:
  - Status: completed
  - Implemented standalone parser ownership boundaries in code and kept watchdog health separate.

## Task 2
- Goal:
  - Specify source priority, normalization rules, and degraded behavior for the first parser implementation.
- Files:
  - [code_copilot/changes/build-codex-transcript-parser/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/spec.md)
  - [code_copilot/changes/build-codex-transcript-parser/parser-design.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/parser-design.md)
- Verification:
  - Confirm the design supports missing structured sources and can still emit a valid snapshot.
- Notes:
  - Status: completed
  - Implemented raw-log fallback with `degraded` parser state and normalized `current_summary`.

## Task 3
- Goal:
  - Record the minimal v1 execution plan and the first test matrix so the next implementation change can proceed without reopening scope.
- Files:
  - [code_copilot/changes/build-codex-transcript-parser/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/log.md)
  - [code_copilot/changes/build-codex-transcript-parser/parser-design.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/parser-design.md)
- Verification:
  - Confirm the doc includes phased implementation and fixture-driven tests.
- Notes:
  - Status: completed
  - Added parser tests and wired parser startup/shutdown into watchdog lifecycle scripts.

## Resume Checklist

- Last touched files:
  - [code_copilot/changes/build-codex-transcript-parser/spec.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/spec.md)
  - [code_copilot/changes/build-codex-transcript-parser/tasks.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/tasks.md)
  - [code_copilot/changes/build-codex-transcript-parser/log.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/log.md)
  - [code_copilot/changes/build-codex-transcript-parser/parser-design.md](/Users/zhang/Desktop/agent-watchdog/code_copilot/changes/build-codex-transcript-parser/parser-design.md)
- Last verification command:
  - `python3 -m unittest tests/test_codex_session_parser.py`
  - `python3 -m unittest discover -s tests`
- Last known failing point:
  - None. Parser tests and full suite are green.
