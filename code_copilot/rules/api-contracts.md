# API Contracts

This repository has no HTTP API. The primary contracts are runtime files and shell entry points.

## Runtime File Contracts

- `runtime/status.json`
  - Main watchdog state consumed by `scripts/status.py` and operator tooling
  - Field additions are acceptable when backward compatible
  - Field renames, removals, or meaning changes require docs and tests to move together
- `runtime/launch.json`
  - Current managed task metadata such as command, log path, session, pane, and restart inputs
  - Writers and readers must agree on key names because restart scripts depend on this file
- `runtime/events.log`
  - Append-only JSON lines
  - Event names should remain stable once introduced

## CLI Contracts

- `scripts/aww`, `scripts/awx`, and `scripts/awxbar` are operator entry points for launching managed tasks.
- `scripts/start_watchdog.sh`, `scripts/stop_watchdog.sh`, `scripts/restart.sh`, `scripts/tmux_launch.sh`, and `scripts/tmux_restart.sh` form the operational control surface.
- Shell command changes should preserve existing invocation style unless there is a clear migration path.

## Contract Stability Rules

- Keep runtime field names stable across producers and consumers.
- Record default-value behavior explicitly when introducing new status fields.
- Prefer additive changes over semantic rewrites.
- If a contract change affects documentation or HUD rendering, update the docs and corresponding tests in the same change package.
