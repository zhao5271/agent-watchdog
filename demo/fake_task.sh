#!/usr/bin/env bash
set -euo pipefail
LOG_FILE="/Users/zhang/Desktop/agent-watchdog/demo/task.log"
printf '初始化任务\n' >> "$LOG_FILE"
sleep 2
printf '正在执行首页重构\n' >> "$LOG_FILE"
sleep 2
printf '开始验证前端测试\n' >> "$LOG_FILE"
sleep 2
printf '任务完成\n' >> "$LOG_FILE"
sleep 60
