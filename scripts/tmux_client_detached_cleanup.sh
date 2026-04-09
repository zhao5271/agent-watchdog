#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="${1:-}"

if [[ -z "$SESSION_NAME" ]]; then
  exit 0
fi

if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  exit 0
fi

ATTACHED_COUNT="$(tmux display-message -p -t "$SESSION_NAME" '#{session_attached}' 2>/dev/null || printf '0')"
if [[ "$ATTACHED_COUNT" == "0" ]]; then
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
fi
