# Mini Agent Learn

一个从零构建的 AI 编程助手，模仿 Claude Code 的 Agentic 工作模式，用于个人学习与实践。

## 项目简介

这是个人学习项目，旨在通过动手实现来深入理解 AI Agent 的核心原理。项目实现了一个完整的多 Agent 编程助手，支持工具调用、团队协作、持久化记忆、联网搜索等功能，所有能力均由 OpenAI 兼容 API 驱动。支持 CLI 模式和 Web 服务模式。

## 功能特性

- **Agentic 循环** — LLM 调用 → 工具执行 → 结果反馈 → 继续推理，直到任务完成
- **丰富的工具集** — 文件读写编辑、Bash 命令执行、联网搜索与网页抓取、任务管理、记忆系统
- **多 Agent 协作** — 支持生成一次性子 Agent 和持久化队友，通过消息总线协同工作
- **上下文压缩** — 工具结果摘要 + LLM 自动总结，防止上下文窗口溢出
- **权限管理** — 规则化的工具权限控制，敏感操作交互式确认
- **持久化记忆** — 跨会话的用户偏好、项目上下文、反馈记录
- **会话持久化** — 完整对话历史保存与恢复
- **技能系统** — 可扩展的 Markdown 技能文件，支持热加载
- **后台任务** — Bash 命令后台执行与状态追踪
- **双模式运行** — CLI 终端模式和 Web 服务模式，共享核心 Agent 逻辑

## 架构概览

```
main.py (入口)
  │
  ├─→ CLI 模式 (默认)
  │     REPL 循环 → CliOutputHandler → ANSI 彩色终端输出
  │
  └─→ Web 模式 (--web)
        service/main.py → FastAPI
          │
          ├─→ SSE 流式推送 (/api/chat/stream)
          ├─→ 轮询式获取 (/api/runs/events)
          └─→ 会话管理 (SessionManager)
                │
                └─→ ServiceOutputHandler → 事件列表 + 订阅通知

Agent (核心循环)
  │
  ├─→ OpenAI 兼容 API (可配置 BASE_URL / MODEL)
  │
  ├─→ 工具调度 (TOOL_MAPPER)
  │     ├─ 文件操作 (read_file / write_file / edit_file)
  │     ├─ Bash 执行 (沙箱化，安全校验)
  │     ├─ 任务管理 (TaskManager → .tasks/)
  │     ├─ 记忆系统 (MemoryManager → .memory/)
  │     ├─ 后台任务 (BackgroundManager → .runtime-tasks/)
  │     ├─ 联网工具 (DuckDuckGo 搜索 + 网页抓取)
  │     ├─ 技能加载 (SkillLoader → skills/)
  │     └─ 团队协作 (MessageBus + TeammateManager)
  │
  ├─→ 子 Agent (spawn_agent → 独立上下文的一次性 Agent)
  │
  ├─→ 权限管理 (PermissionManager)
  │
  └─→ 上下文压缩 (工具结果摘要 + LLM 总结)
```

## 工具分层

| 层级 | 工具 | 说明 |
|------|------|------|
| **BASE_TOOLS** | bash, read_file, write_file, edit_file, todo, load_skill, compression, web_search, web_fetch | 所有 Agent 可用 |
| **BUS_TOOLS** | send_message, read_inbox | 团队消息通信 |
| **PARENT_TOOLS** | BASE + BUS + spawn_agent, save_memory, task_create/update/list/get/del, background_run, check_background, spawn_teammate, list_teammates, broadcast | 主 Agent 专属 |

## 快速开始

### 环境要求

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) 包管理器
- Node.js >= 18（Web 模式前端）

### 安装

```bash
git clone <repo-url>
cd code-agent-learn
uv sync
```

### 配置

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your-api-key
BASE_URL=https://api.openai.com/v1   # 或其他兼容端点
MODEL=gpt-4o                          # 或其他模型
```

### 运行

```bash
# CLI 模式（默认）
uv run main.py

# Web 服务模式（后端 + 前端分别启动）
uv run main.py --web          # 启动后端 API（端口 8000）
cd web && npm install         # 安装前端依赖
cd web && npm run dev         # 启动前端（端口 5173，代理 /api 到 8000）
```

### CLI REPL 命令

| 命令 | 说明 |
|------|------|
| `exit` / `quit` / `q` | 退出程序 |
| `clear` | 清空对话历史 |
| `history` | 查看当前对话 |
| `memories` | 查看持久化记忆 |
| `restore` | 恢复之前的会话 |

## 项目结构

```
code-agent-learn/
├── main.py                    # 入口：CLI 默认，--web 启动服务模式
├── service/
│   ├── main.py                # Web 服务启动入口
│   ├── app.py                 # FastAPI 应用和端点
│   └── session.py             # Session/RunState/SessionManager 会话管理
├── agents/
│   ├── agent.py               # 核心 Agent 类与主循环
│   ├── tools.py               # 工具定义与调度映射
│   ├── output_handler.py      # I/O 解耦：CliOutputHandler / ServiceOutputHandler
│   ├── sub_agent.py           # 子 Agent 生成
│   ├── prompt.py              # 系统提示词构建
│   ├── task.py                # 持久化任务管理
│   ├── todo.py                # 内存待办清单
│   ├── teams.py               # 多 Agent 团队协作
│   ├── background_task.py     # 后台任务执行
│   └── utils/
│       ├── BashSecurityValidator.py  # Bash 命令安全校验
│       ├── Memory.py                 # 持久化记忆管理
│       ├── Permission.py             # 权限管理
│       ├── context_compression.py    # 上下文压缩
│       ├── skill_loader.py           # 技能加载器
│       ├── transcript.py             # 会话持久化
│       ├── watch_skill.py            # 技能文件热加载
│       └── web_tools.py              # 联网搜索与抓取
├── web/                        # React 前端（Vite + TypeScript）
│   └── src/
│       ├── App.tsx             # 主组件
│       ├── api.ts              # API 调用封装
│       ├── types.ts            # 类型定义
│       ├── hooks/              # React hooks（事件轮询等）
│       └── components/         # UI 组件
├── skills/                     # 技能目录（Markdown 格式）
├── .memory/                    # 持久化记忆存储
├── .tasks/                     # 持久化任务存储
├── .transcripts/               # 会话历史存储
└── .runtime-tasks/             # 后台任务运行时数据
```

## 安全机制

- **Bash 安全校验** — 自动拦截 `sudo`、`rm -rf` 等危险命令
- **文件沙箱** — 文件操作限制在工作目录内
- **权限管理** — 规则化的工具访问控制，CLI 模式未匹配操作需用户交互确认，Web 模式自动允许（危险命令仍由 BashSecurityValidator 拒绝）

## 学习要点

本项目覆盖了构建 AI Agent 的核心知识点：

1. **Tool Use** — 工具定义、调度、结果回传的完整流程
2. **Agentic Loop** — LLM 驱动的自主决策与循环执行
3. **Multi-Agent** — 子 Agent、团队协作、消息通信
4. **Context Management** — 长对话压缩与上下文窗口管理
5. **Persistence** — 记忆、任务、会话的跨会话持久化
6. **Safety** — 权限控制与安全校验
7. **I/O Decoupling** — OutputHandler 模式实现 CLI/Web 双模式输出

## License

MIT