# Knowledge Index

- `scripts/watchdog.py` is the state producer. It inspects process liveness, log tail content, timeouts, and tmux pane state, then writes `runtime/status.json` and `runtime/events.log`.
- `scripts/status.py` is the read-only terminal renderer. It turns `status.json` into a one-shot or watch-mode HUD.
- The repository intentionally favors conservative monitoring. It should avoid overclaiming progress or auto-restarting too aggressively.
- `runtime/` is operational scratch space, not a durable project artifact.
- The product's current testing style uses direct file loading with `importlib.util.spec_from_file_location`, which means refactors around script paths need test updates.

## Suggested Topics

- status and stage semantics
- tmux session archival and replacement rules
- timeout and restart policy edge cases
- runtime file compatibility expectations
- terminal HUD formatting expectations
