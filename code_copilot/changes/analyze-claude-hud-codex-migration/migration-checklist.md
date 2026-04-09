# claude-hud 到 Codex 的迁移层清单

## 结论

`claude-hud` 不是单纯的“状态栏皮肤”，而是四层一起工作：

1. Claude Code 原生接入层
2. Claude 会话遥测采集层
3. Transcript 结构化解析层
4. 可配置渲染层

`awx` 当前已经把“本地任务托管 + tmux 生命周期 + 看板渲染”做出来了，但它还没有 Codex 版本的“结构化会话遥测层”。
真正的迁移重点不在 HUD 样式，而在“如何把 Codex 会话变成可结构化消费的状态快照”。

## 分层对照

| 层 | `claude-hud` 怎么做 | 迁移到 Codex 需要改什么 | `awx` 当前状态 | 结论 |
| --- | --- | --- | --- | --- |
| 1. 集成入口层 | 通过 Claude Code `statusLine` 命令调用，插件清单见 `.claude-plugin/plugin.json`，安装/写入由 `commands/setup.md` 负责 | 改成 Codex 可用入口。大概率不能复用 Claude 插件机制，要改成 `awx` 这种 wrapper/launcher 或新的本地 adapter | `awx` / `aww` / `tmux_launch.sh` 已经能托管命令、挂 status-right、控制生命周期 | 已实现一半。入口有了，但不是原生 Codex 扩展点 |
| 2. 输入契约层 | `src/stdin.ts` 读取 Claude Code stdin JSON，字段包括 `cwd`、`transcript_path`、`model`、`context_window`、`cost`、`rate_limits` | 为 Codex 定义等价快照来源。需要明确从哪里拿模型、上下文、tokens、usage、session 标识 | `awx` 当前只有 `launch.json` + `status.json`，缺模型、token、usage、cost | P0 缺层 |
| 3. Transcript 解析层 | `src/transcript.ts` 解析 transcript JSONL，提取 tools、agents、todos、session tokens，并做缓存 | 为 Codex 写新的结构化 parser，不能直接复用 Claude transcript 语义 | `awx` 只做 `recent_output` 抓取和阶段关键词推断，没有结构化工具/子代理/待办模型 | P0 缺层 |
| 4. 配置与规则发现层 | `src/config-reader.ts` 统计 `CLAUDE.md`、rules、MCP、hooks、`outputStyle` | 映射到 Codex 生态。可能对应 `code_copilot/rules`、skills、plugins、MCP 资源、workspace 规则 | `awx` 没有这一层，只知道 project 路径 | P2 缺层，价值次于遥测 |
| 5. Git/工作区元数据层 | `src/git.ts` 提供 branch、dirty、ahead/behind、file stats | 直接可迁移，和 Claude 无强绑定 | `awx` 有 project 元数据写入 `launch.json`，但 HUD 没展示 git 状态 | P1 缺层 |
| 6. 渲染编排层 | `src/render/index.ts` 负责 expanded/compact、换行、宽度、element order、分隔线 | 可以复用思路，但实现要对接 Codex 数据模型 | `awx` 已有 `status.py` 的多行/单行 HUD，但是固定布局、固定字段 | 已实现基础版，但可配置性明显不足 |
| 7. 活动部件层 | tools line、agents line、todos line 分别渲染 | Codex 需要等第 2/3 层就绪后才能做 | `awx` 只有 recent output 详情块，没有独立工具/agent/todo 部件 | P1 缺层 |
| 8. 用户配置层 | `src/config.ts` + `commands/configure.md` 支持布局、语言、显示项、颜色、preset | Codex 侧要决定是 JSON 配置、环境变量、还是交互式命令 | `awx` 目前偏硬编码，只支持少量环境变量，主要控制 launcher 而非 HUD 元素 | P2 缺层 |
| 9. 安装/配置 UX 层 | `commands/setup.md` 自动检测 runtime、平台、插件路径、写 settings.json | 改为 `awx setup` 或独立 bootstrap，不能复用 Claude 插件 setup | `awx` 目前靠 README + shell script，没有 guided setup | P2 缺层 |
| 10. 缓存/性能层 | transcript/config cache，避免每次刷新全量解析 | 如果 Codex 日志/事件量大，这层要一起做 | `awx` 目前轮询简单状态足够，但一旦引入结构化解析就不够了 | P1 预备层 |
| 11. 跨平台层 | setup 流程显式处理 macOS/Linux/Windows/Git Bash/PowerShell | Codex 迁移如果只跑本机 tmux，可先不做；若要通用，则必须补 | `awx` 路径和运行方式明显偏本机、偏 tmux、偏 macOS/Linux | P2 缺层 |
| 12. 任务托管与恢复层 | `claude-hud` 基本没有；它依赖 Claude Code 自身生命周期 | 这一层不用迁移，反而应保留 `awx` 优势 | `awx` 的 `watchdog.py`、`tmux_restart.sh`、session archival 已成熟 | `awx` 明显强于 `claude-hud` |

## 结合 `awx` 当前能力后的判断

### 已经实现，应该保留

- 任务托管与附着工作流：`scripts/awx`、`scripts/aww`、`scripts/tmux_launch.sh`
- 本地 runtime 真相层：`runtime/launch.json`、`runtime/status.json`、`runtime/events.log`
- 健康检测和恢复：`scripts/watchdog.py`
- 单行和多行 HUD：`scripts/status.py`
- 最近输出清洗与阶段型状态：`recent_output`、stage rules、`status-right` 摘要

### 已经有雏形，但还不够

- HUD 渲染层：已经能输出，但没有 element order、preset、主题、颜色、语言切换、宽度策略
- 上下文细节层：现在只有 recent output，不是结构化的 tool/agent/todo
- 项目元数据层：当前只有 command summary 和 project path，没有 git/workspace/config counts

### 明显缺失，是迁移关键

- Codex 会话输入契约
- Codex transcript / event parser
- 结构化 tools / agents / todos 数据模型
- token / context / usage / cost 数据源
- 配置发现与规则统计
- 可配置 HUD 配置文件和 guided setup

## 推荐迁移顺序

### P0

- 先定义 Codex session snapshot 格式
- 再做 Codex transcript/event parser
- 把 parser 输出落为本地结构化状态文件，而不是直接耦合到 HUD

### P1

- 基于结构化状态，补 tools / agents / todos 组件
- 补 git/workspace 元数据
- 加缓存层，避免每次刷新全量解析 Codex 日志

### P2

- 做配置文件、preset、语言和颜色
- 做 setup/bootstrap UX
- 再考虑跨平台支持、多任务面板、HTML 页面、通知渠道

## 一个更务实的迁移策略

不要直接“把 `claude-hud` 改成支持 Codex”。
更合适的是保留 `awx` 现有托管能力，只借鉴 `claude-hud` 的中上层设计：

1. 复用 `awx` 的 launcher/watchdog/tmux 生命周期
2. 新增 `codex session adapter`
3. 新增 `codex transcript parser`
4. 把 `status.py` 升级成可消费结构化 activity 的 renderer

这样做的原因：

- `awx` 已经解决了 `claude-hud` 没解决的本地任务托管问题
- `claude-hud` 最值钱的是 Claude 原生 telemetry 消费方式，而不是插件包装
- 直接照搬插件层会把工作做错方向

## 当前最值得开的后续 change

- `define-codex-session-snapshot`
  - 明确 Codex HUD 需要的字段、来源、刷新策略、落盘格式
- `build-codex-transcript-parser`
  - 把工具调用、子代理、todo、token 用量解析成结构化事件
- `upgrade-awx-renderer-to-activity-widgets`
  - 在 `status.py` 里接入 tools/agents/todos/git 等部件

## 来源

- 本仓库：
  - `README.md`
  - `docs/架构说明.md`
  - `scripts/awx`
  - `scripts/tmux_launch.sh`
  - `scripts/watchdog.py`
  - `scripts/status.py`
- `claude-hud`：
  - `src/index.ts`
  - `src/stdin.ts`
  - `src/transcript.ts`
  - `src/render/index.ts`
  - `src/config.ts`
  - `src/config-reader.ts`
  - `src/git.ts`
  - `.claude-plugin/plugin.json`
  - `commands/setup.md`
  - `commands/configure.md`
