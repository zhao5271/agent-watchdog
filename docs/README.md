# 学习文档索引

这个目录用来帮助你从“会用”进入“看懂”。

如果你是把 `agent-watchdog` 当作学习样例，建议按下面顺序阅读。

## 推荐阅读顺序

### 1. 先看整体架构

- [架构说明.md](/Users/zhang/Desktop/agent-watchdog/docs/架构说明.md)

先理解：

- 为什么这个工具要拆成 `config / scripts / runtime / docs`
- 为什么它只监控、不自动重启
- `status.json`、`events.log`、HUD 的关系是什么

### 2. 再看状态模型

- [状态字段说明.md](/Users/zhang/Desktop/agent-watchdog/docs/状态字段说明.md)

这一份最适合先把核心数据字段看懂：

- `status`
- `stage`
- `idle_seconds`
- `suggest_restart`

### 3. 再看脚本职责

- [脚本职责说明.md](/Users/zhang/Desktop/agent-watchdog/docs/脚本职责说明.md)

这里会告诉你：

- 每个脚本负责什么
- 脚本之间是怎么配合的
- 哪个脚本是后台常驻核心

### 4. 最后看阅读顺序

- [阅读顺序.md](/Users/zhang/Desktop/agent-watchdog/docs/阅读顺序.md)

如果你准备开始读源码，这份最有帮助。

## 最值得优先理解的点

### 1. 这个工具的主真相不是终端输出，而是 `runtime/status.json`

HUD 只是展示层。

### 2. `watchdog.py` 是唯一后台常驻核心

其他脚本都是入口、展示或执行器。

### 3. 这个工具故意不自动重启

这是最重要的产品决策之一。
