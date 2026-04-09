# Agent Watchdog

一个放在本地后台运行的任务监听器，用于：

- 监听单个任务是否仍在运行
- 通过日志推断任务阶段
- 识别任务是否变慢、疑似卡住、意外停止
- 在终端中以 HUD 风格展示状态
- 提示你是否需要手动重启任务

## 当前能力

- 单任务监听
- `tmux` 托管任务
- 保留失败现场后自动拉起 replacement session
- 状态文件 `runtime/status.json`
- 启动元数据 `runtime/launch.json`
- 事件日志 `runtime/events.log`
- 终端 HUD 展示
- 手动重启命令

## 目录

```text
agent-watchdog/
├── README.md
├── config/
│   ├── stage-rules.json
│   └── tasks.example.json
├── docs/
│   └── 状态字段说明.md
├── runtime/
│   ├── events.log
│   ├── status.json
│   └── watchdog.pid
└── scripts/
    ├── restart.sh
    ├── status.py
    └── watchdog.py
```

## 快速开始

### 1. 最简启动

```bash
aww "python3 /path/to/task.py"
```

如果你希望启动后立刻进入交互 session，用：

```bash
awx "codex"
```

如果你想对比状态栏 HUD，用：

```bash
awxbar "codex"
```

说明：

- 启动前会先停掉这个仓库里的旧 watchdog，避免多个进程同时覆盖状态文件
- 任务会进入新的 `tmux session`
- 输出会写入新的运行日志文件
- `watchdog` 会读取 `runtime/launch.json`，跟踪当前活跃 session/pane
- 如果任务 `failed / stopped / stalled`，会先把旧 session 重命名成 `*-failed-时间戳`，再拉起新的 replacement session
- 默认参数：
  - `soft_timeout=300`
  - `hard_timeout=900`
  - `poll_interval=5`
  - `max_restarts=3`

### 2. 可选环境变量

```bash
AWW_TASK_NAME="首页重构" AWW_MAX_RESTARTS=5 aww "python3 /path/to/task.py"
```

支持：

- `AWW_TASK_NAME`
- `AWW_SOFT_TIMEOUT`
- `AWW_HARD_TIMEOUT`
- `AWW_POLL_INTERVAL`
- `AWW_MAX_RESTARTS`

### 3. 三个入口的区别

- `aww "命令"`
  启动托管任务，但不自动进入 session
- `awx "命令"`
  启动托管任务后，立刻 `tmux attach`，并分一个 HUD pane
- `awxbar "命令"`
  启动托管任务后，立刻 `tmux attach`，并把 HUD 放进 `tmux status-right`

### 4. 高级用法

如果你要手动指定 `task-id`、`session-prefix` 或更底层参数，再直接调用：

```bash
bash /Users/zhang/Desktop/agent-watchdog/scripts/tmux_launch.sh \
  --task-id home-redesign \
  --task-name "首页结果工作台重构" \
  --command "python3 /path/to/task.py"
```

### 5. 查看状态

```bash
python3 /Users/zhang/Desktop/agent-watchdog/scripts/status.py
```

持续刷新：

```bash
python3 /Users/zhang/Desktop/agent-watchdog/scripts/status.py --watch
```

### 6. 停止监听

```bash
bash /Users/zhang/Desktop/agent-watchdog/scripts/stop_watchdog.sh
```

### 7. 手动执行重启

```bash
bash /Users/zhang/Desktop/agent-watchdog/scripts/restart.sh
```

它会读取 `runtime/launch.json`，保留当前失败现场后再新建一个 session。

## 关键运行文件

- `runtime/status.json`
  HUD 和其他脚本读取的主状态
- `runtime/launch.json`
  当前被托管的 `tmux session / pane / command / log_path`
- `runtime/events.log`
  `watchdog_started / stage_changed / task_restarted / restart_failed`

## 设计原则

### 对 `tmux` 现场友好

自动恢复时会：

- 保留旧 session
- 把旧 session 重命名成 `*-failed-时间戳`
- 让你可以随时 `tmux attach -t <旧session>` 回看现场

### 自动重启有上限

默认最多自动恢复 3 次，避免错误配置导致无限重启。

### `graphModel` 一类数据无关

这个工具不绑定某个具体项目的数据结构。
它只关心：

- 进程
- `tmux session / pane`
- 日志
- 阶段
- 超时

## 下一步可以扩展的能力

- 多任务面板
- HTML 状态页
- 系统服务化运行
- 通知渠道（Telegram / 飞书 / 邮件）
