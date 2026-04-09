#!/usr/bin/env bash
set -uo pipefail

if [[ -z "${TASK_COMMAND_B64:-}" ]]; then
  echo "缺少 TASK_COMMAND_B64"
  exit 1
fi

TASK_RUNNER_START_DELAY="${TASK_RUNNER_START_DELAY:-0.2}"
TASK_COMMAND="$(printf '%s' "$TASK_COMMAND_B64" | base64 --decode)"

sleep "$TASK_RUNNER_START_DELAY"
bash -lc "$TASK_COMMAND"
EXIT_CODE=$?

printf '__TASK_EXIT_CODE__=%s\n' "$EXIT_CODE"
exit "$EXIT_CODE"
