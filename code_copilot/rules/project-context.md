# Project Context

- Project name: Agent Watchdog
- Identifier: agent-watchdog
- Runtime or language: python
- Backend stack: local watchdog daemon + tmux
- Frontend stack: none
- Primary database: none
- Cache: none
- Async stack: polling loop + tmux session orchestration
- Default test command: python3 -m unittest discover -s tests

## Directory Notes

- `scripts/` holds the executable behavior for the product. Core logic lives in `scripts/watchdog.py` and display logic lives in `scripts/status.py`.
- Shell entry points in `scripts/` wrap tmux session setup, watchdog start and stop, and restart behavior. Main operator-facing commands are `aww`, `awx`, `awxbar`, `start_watchdog.sh`, `stop_watchdog.sh`, and `restart.sh`.
- `runtime/` is runtime state only. It contains mutable process metadata, pid files, logs, and watchdog state such as `status.json`, `launch.json`, and `events.log`. These files are not source of record for repository code and should stay ignored by git.
- `config/` contains static configuration and rule files such as `stage-rules.json` and example task config.
- `tests/` uses Python `unittest` and loads scripts directly from `scripts/` by file path rather than importing a package.
- `docs/` contains operator and architecture documentation and should be updated when behavior or status fields change.

## Suggested Mapping

- App entry points:
  - `scripts/watchdog.py`: polling watchdog loop and runtime state producer
  - `scripts/status.py`: terminal HUD and status formatter
  - `scripts/tmux_launch.sh`: tmux-backed task bootstrap
  - `scripts/tmux_restart.sh`: tmux replacement-session restart flow
- Domain modules:
  - task liveness detection
  - log tail parsing
  - stage inference
  - timeout and restart policy
  - tmux session and pane inspection
- API layer:
  - none in the HTTP sense
  - file contracts in `runtime/status.json`, `runtime/launch.json`, and `runtime/events.log`
  - shell CLI contracts via scripts in `scripts/`
- Persistence layer:
  - filesystem only
  - JSON files and append-only log files under `runtime/`
- Jobs, queues, or async workers:
  - single watchdog polling loop in `scripts/watchdog.py`
  - monitored task runs inside tmux and is treated as an external workload
- UI, mobile, or client apps:
  - terminal HUD only
  - no browser or native UI
- Build, test, and deployment files:
  - tests: `python3 -m unittest discover -s tests`
  - no package build pipeline yet
  - deployment is local-machine execution through shell and tmux
