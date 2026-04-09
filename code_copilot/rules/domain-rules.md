# Domain Rules

- The product monitors a task conservatively. It should observe process, log output, elapsed time, and tmux state without pretending to understand the task's business semantics.
- `status` and `stage` are different concepts and must remain separate.
- `status` is the machine judgment such as `running`, `slow`, `stalled`, `stopped`, `completed`, or `failed`.
- `stage` is a human-readable progress label inferred from recent output, such as `准备中`, `执行中`, `验证中`, or `完成`.
- `runtime/status.json` is the main machine-readable state for HUD and helper scripts.
- `runtime/launch.json` describes the current managed task session and restart inputs.
- `runtime/events.log` is an append-only event stream for watchdog decisions and lifecycle events.
- `runtime/` contents are ephemeral operational state. Code changes must not depend on committing those files to git.

## Suggested Sections

### Contract Rules

- File contract changes in `status.json`, `launch.json`, or event payloads are breaking changes unless docs, readers, and tests are updated together.
- Operator-facing shell entry points should stay simple and explicit. Favor flags or environment variables over hidden behavior.
- `status.py` is a read-only consumer of runtime state. It must not become the place that mutates watchdog state.

### Data Rules

- Source code lives outside `runtime/`; runtime files are generated and replaceable.
- `config/` owns static rules and examples. If stage inference behavior changes, prefer updating config or documenting the reason when code changes are needed.
- Documentation in `docs/` should be kept consistent with actual runtime fields and operator commands.

### Async Rules

- Watchdog polling is periodic and should tolerate missing files, stale pids, and dead tmux panes without crashing.
- Restart behavior is bounded. Auto-restart must respect `max_restarts`, cooldown checks, and restartable statuses.
- A restart should preserve failure context when possible, for example by archiving or renaming the failed tmux session before replacement.
- Avoid infinite recovery loops. Any change that broadens restart conditions needs explicit justification and tests.

### Frontend or Client Rules

- The terminal HUD should remain lightweight and derived entirely from runtime state.
- Display formatting changes belong in `scripts/status.py` and should not leak monitoring policy into the renderer.
