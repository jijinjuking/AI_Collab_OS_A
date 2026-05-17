# AI-Collab-OS 模块架构设计

## 技术栈确认

| 层 | 技术 | 版本 |
|---|------|------|
| 后端框架 | FastAPI | 0.115+ |
| Agent 编排 | LangGraph | 0.2+ |
| LLM 适配 | LiteLLM | 1.40+ |
| ORM | SQLModel | 0.0.16+ |
| 数据库 | PostgreSQL / SQLite | 16+ / 3.x |
| 缓存/消息 | Redis | 7+ |
| 前端框架 | React + TypeScript | 18+ / 5+ |
| 构建工具 | Vite | 5+ |
| 状态管理 | Zustand | 4+ |
| 代码编辑器 | Monaco Editor | 0.44+ |
| 工作流可视化 | React Flow | 11+ |
| 移动端 | PWA (响应式 Web) | - |
| WebSocket | FastAPI WebSocket + Redis Pub/Sub | - |
| 代码沙箱 | Docker-in-Docker / Docker SDK | - |
| 容器化 | Docker + Docker Compose | - |
| Python | 3.11+ | - |
| Node.js | 20+ (前端构建) | - |

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端 (Browser)                       │
│  React + TypeScript + Vite                                   │
│  ┌──────────┬──────────┬──────────┬──────────┐              │
│  │ IDE 布局  │ Agent 面板│ 工作流编辑│ 文件管理  │              │
│  │ (Monaco) │ (对话流)  │(ReactFlow)│ (文件树)  │              │
│  └──────────┴──────────┴──────────┴──────────┘              │
│  Zustand Store ←→ WebSocket Client ←→ REST API Client        │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP + WebSocket
┌──────────────────────────┴───────────────────────────────────┐
│                     API 网关 (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Routers: auth | projects | agents | workflows |         │  │
│  │          messages | files | roles | api-keys | logs     │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ WebSocket Hub: 连接管理 | 房间(项目频道) | 消息广播       │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Middleware: JWT Auth | CORS | Rate Limit | Error Handler│  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                    业务服务层 (Services)                        │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │ Agent    │ Workflow  │ File     │ Communication        │  │
│  │ Service  │ Service   │ Service  │ Service              │  │
│  │          │           │          │ (消息路由/持久化)     │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                  Agent 编排引擎 (LangGraph)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Graph Builder: 根据 DAG 配置动态构建状态图                 │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ Node Types:                                             │  │
│  │  - ExecuteNode: Agent 执行任务                           │  │
│  │  - DiscussNode: 两个 Agent 互相讨论                      │  │
│  │  - AssignNode: 架构师分配任务给多个 Agent                 │  │
│  │  - ReviewNode: 审查员审查 + 打回循环                     │  │
│  │  - GateNode: 条件分支（通过/打回/升级）                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ State: 共享状态（任务书、产出物、审查结果、文件列表）       │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ Checkpointer: 状态持久化（断点恢复）                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                    LLM 适配层 (LiteLLM)                        │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │ OpenAI   │Anthropic │ Ollama   │ Custom (任意兼容端点)  │  │
│  │ GPT-4o   │Claude 3.5│ Llama3   │ DeepSeek/Qwen/...    │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
│  Token 计数 | 流式输出 | 重试策略 | 费用追踪                   │
└──────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                      持久化层                                  │
│  ┌──────────┬──────────┬──────────────────────────────────┐  │
│  │PostgreSQL│  Redis   │  文件系统 (Git Repo)              │  │
│  │ 结构数据  │ Pub/Sub  │  /workspaces/<project_id>/       │  │
│  │ 消息历史  │ 缓存     │    ├── committed/ (正式代码)      │  │
│  │ 用户/项目 │ 会话状态  │    ├── drafts/ (草稿)            │  │
│  │          │ 任务队列  │    └── .git/ (版本管理)           │  │
│  └──────────┴──────────┴──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 模块职责定义

### 1. API 层 (api/)
- 接收 HTTP/WebSocket 请求
- 参数校验 (Pydantic)
- 调用 Service 层
- 返回标准响应
- 不含业务逻辑

### 2. Service 层 (services/)
- 核心业务逻辑
- 跨模块协调
- 事务管理
- 事件发布

### 3. Agent 引擎层 (engine/)
- LangGraph 状态图构建
- 节点执行逻辑
- Agent 间消息路由
- 工作流状态管理
- LLM 调用封装

### 4. 数据层 (db/)
- SQLModel 模型定义
- 数据库会话管理
- 迁移脚本

### 5. 基础设施层 (core/)
- 配置管理
- 安全工具 (JWT, 加密)
- Redis 客户端
- WebSocket 管理
- 日志

---

## 文件结构

```
ai-collab-platform/
├── docs/                          # 设计文档
│   ├── PRD.md
│   ├── DATABASE_DESIGN.md
│   ├── API_DESIGN.md
│   └── ARCHITECTURE.md            # 本文件
│
├── backend/                       # Python 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 入口，挂载路由
│   │   ├── config.py              # 配置管理 (pydantic-settings)
│   │   │
│   │   ├── api/                   # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── deps.py            # 依赖注入 (get_db, get_current_user)
│   │   │   ├── auth.py            # 认证路由
│   │   │   ├── projects.py        # 项目路由
│   │   │   ├── agents.py          # Agent 实例路由
│   │   │   ├── workflows.py       # 工作流路由
│   │   │   ├── messages.py        # 消息路由
│   │   │   ├── files.py           # 文件管理路由
│   │   │   ├── roles.py           # 角色模板路由
│   │   │   ├── api_keys.py        # API Key 管理路由
│   │   │   └── logs.py            # 活动日志路由
│   │   │
│   │   ├── services/              # 业务服务层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py    # 认证服务 (注册/登录/JWT)
│   │   │   ├── project_service.py # 项目管理服务
│   │   │   ├── agent_service.py   # Agent 实例管理
│   │   │   ├── workflow_service.py# 工作流管理
│   │   │   ├── message_service.py # 消息持久化与查询
│   │   │   ├── file_service.py    # 文件管理 (CRUD + Git)
│   │   │   ├── file_lock_service.py # 文件锁 + 冲突检测
│   │   │   ├── sandbox_service.py # Docker 沙箱管理 (创建/执行/销毁)
│   │   │   ├── role_service.py    # 角色模板管理
│   │   │   └── llm_service.py     # LLM 调用封装 (LiteLLM)
│   │   │
│   │   ├── engine/                # Agent 编排引擎
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py   # DAG → LangGraph 状态图
│   │   │   ├── state.py           # 共享状态定义
│   │   │   ├── nodes/             # 节点类型
│   │   │   │   ├── __init__.py
│   │   │   │   ├── execute.py     # 执行节点
│   │   │   │   ├── discuss.py     # 讨论节点
│   │   │   │   ├── assign.py      # 任务分配节点
│   │   │   │   ├── review.py      # 审查节点
│   │   │   │   └── gate.py        # 条件分支节点
│   │   │   ├── prompts/           # Prompt 模板
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py        # 基础 prompt 构建
│   │   │   │   ├── team_context.py# 团队目录注入
│   │   │   │   └── templates.py   # 角色 prompt 模板
│   │   │   ├── checkpointer.py    # 状态持久化
│   │   │   └── runner.py          # 工作流执行器
│   │   │
│   │   ├── db/                    # 数据层
│   │   │   ├── __init__.py
│   │   │   ├── session.py         # 数据库会话管理
│   │   │   ├── models/            # SQLModel 模型
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── project.py
│   │   │   │   ├── role_template.py
│   │   │   │   ├── project_agent.py
│   │   │   │   ├── workflow.py
│   │   │   │   ├── workflow_step.py
│   │   │   │   ├── agent_message.py
│   │   │   │   ├── project_file.py
│   │   │   │   ├── api_key.py
│   │   │   │   └── activity_log.py
│   │   │   └── migrations/        # Alembic 迁移
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │
│   │   ├── core/                  # 基础设施
│   │   │   ├── __init__.py
│   │   │   ├── security.py        # JWT + 密码哈希 + AES 加密
│   │   │   ├── redis.py           # Redis 客户端
│   │   │   ├── websocket.py       # WebSocket 连接管理
│   │   │   ├── events.py          # 事件总线 (Redis Pub/Sub)
│   │   │   ├── exceptions.py      # 自定义异常
│   │   │   └── logging.py         # 日志配置
│   │   │
│   │   └── schemas/               # Pydantic 请求/响应模型
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── project.py
│   │       ├── agent.py
│   │       ├── workflow.py
│   │       ├── message.py
│   │       ├── file.py
│   │       └── common.py          # 通用响应模型
│   │
│   ├── tests/                     # 测试
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_agents.py
│   │   ├── test_workflows.py
│   │   └── test_engine.py
│   │
│   ├── alembic.ini                # Alembic 配置
│   ├── pyproject.toml             # 项目依赖 (Poetry/uv)
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                      # React 前端
│   ├── src/
│   │   ├── main.tsx               # 入口
│   │   ├── App.tsx                # 根组件
│   │   │
│   │   ├── components/            # UI 组件
│   │   │   ├── layout/            # 布局组件
│   │   │   │   ├── IDELayout.tsx  # 主 IDE 布局
│   │   │   │   ├── Header.tsx     # 顶栏
│   │   │   │   ├── Sidebar.tsx    # 侧边栏
│   │   │   │   ├── StatusBar.tsx  # 底部状态栏
│   │   │   │   └── LogPanel.tsx   # 右侧日志面板
│   │   │   ├── agent/             # Agent 相关
│   │   │   │   ├── AgentPanel.tsx # Agent 工作台
│   │   │   │   ├── AgentChat.tsx  # Agent 对话窗口
│   │   │   │   ├── AgentConfig.tsx# Agent 配置面板
│   │   │   │   ├── AgentCard.tsx  # Agent 卡片
│   │   │   │   └── AgentStatus.tsx# Agent 状态指示
│   │   │   ├── workflow/          # 工作流相关
│   │   │   │   ├── WorkflowEditor.tsx  # DAG 可视化编辑
│   │   │   │   ├── WorkflowStatus.tsx  # 工作流状态面板
│   │   │   │   └── WorkflowControls.tsx# 启动/暂停/停止
│   │   │   ├── files/             # 文件管理
│   │   │   │   ├── FileTree.tsx   # 文件树
│   │   │   │   ├── FileViewer.tsx # 文件查看 (Monaco)
│   │   │   │   └── FileActions.tsx# 文件操作按钮
│   │   │   ├── project/           # 项目管理
│   │   │   │   ├── ProjectPlan.tsx# 项目任务书
│   │   │   │   ├── ProjectList.tsx# 项目列表
│   │   │   │   └── ProjectSettings.tsx
│   │   │   ├── roles/             # 角色管理
│   │   │   │   ├── RoleList.tsx   # 角色列表
│   │   │   │   └── RoleEditor.tsx # 角色编辑器
│   │   │   └── common/            # 通用组件
│   │   │       ├── Modal.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── Tabs.tsx
│   │   │       └── Loading.tsx
│   │   │
│   │   ├── stores/                # Zustand 状态管理
│   │   │   ├── authStore.ts       # 认证状态
│   │   │   ├── projectStore.ts    # 项目状态
│   │   │   ├── agentStore.ts      # Agent 实例状态
│   │   │   ├── workflowStore.ts   # 工作流状态
│   │   │   ├── messageStore.ts    # 消息状态
│   │   │   └── fileStore.ts       # 文件状态
│   │   │
│   │   ├── services/              # API 调用封装
│   │   │   ├── api.ts             # Axios 实例 + 拦截器
│   │   │   ├── authApi.ts
│   │   │   ├── projectApi.ts
│   │   │   ├── agentApi.ts
│   │   │   ├── workflowApi.ts
│   │   │   ├── messageApi.ts
│   │   │   ├── fileApi.ts
│   │   │   └── websocket.ts       # WebSocket 客户端
│   │   │
│   │   ├── hooks/                 # 自定义 Hooks
│   │   │   ├── useWebSocket.ts    # WebSocket 连接管理
│   │   │   ├── useAgent.ts        # Agent 操作
│   │   │   └── useWorkflow.ts     # 工作流操作
│   │   │
│   │   ├── pages/                 # 页面
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx      # 项目列表页
│   │   │   └── Workspace.tsx      # 主工作区（IDE 界面）
│   │   │
│   │   ├── styles/                # 样式
│   │   │   ├── globals.css        # 全局样式 + CSS 变量
│   │   │   ├── ide.css            # IDE 布局样式（从旧项目迁移）
│   │   │   └── agent.css          # Agent 相关样式
│   │   │
│   │   ├── types/                 # TypeScript 类型
│   │   │   ├── agent.ts
│   │   │   ├── workflow.ts
│   │   │   ├── message.ts
│   │   │   └── project.ts
│   │   │
│   │   └── utils/                 # 工具函数
│   │       ├── format.ts          # 格式化
│   │       └── language.ts        # 语言检测 (Monaco)
│   │
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── workspaces/                    # 项目工作区（运行时生成）
│   └── <project_id>/
│       ├── committed/             # 正式代码
│       ├── drafts/                # Agent 草稿
│       └── .git/                  # Git 仓库
│
├── docker-compose.yml             # 一键部署
├── .env.example                   # 环境变量模板
├── Makefile                       # 常用命令
└── README.md                      # 项目说明
```

---

## 模块间通信方式

| 调用方 | 被调用方 | 方式 |
|--------|----------|------|
| 前端 → API | REST HTTP | 同步请求 |
| 前端 ← API | WebSocket | 实时推送 |
| 前端 ← Agent | WebSocket (token stream) | 流式输出 |
| API → Service | 函数调用 | 同步 |
| Service → Engine | 函数调用 (async) | 异步 |
| Engine → LLM | LiteLLM (HTTP) | 异步流式 |
| Engine → WebSocket | Redis Pub/Sub | 事件广播 |
| Service → DB | SQLModel (async) | 异步 |
| Service → Redis | aioredis | 异步 |

---

## 关键设计决策

### 1. 为什么用 LangGraph 而不是自研状态机？
- LangGraph 原生支持有状态图、条件边、循环（审查打回）
- 内置 Checkpointer 支持断点恢复
- 支持动态添加/移除节点
- 社区活跃，文档完善

### 2. 为什么前后端分离？
- 旧项目 server.js 1499 行 + app.js 1916 行，耦合严重
- 前后端分离后可独立部署、独立扩展
- React 生态的组件化能力远超原生 JS

### 3. 为什么用 Redis？
- WebSocket 广播需要 Pub/Sub（多进程部署时）
- Agent 任务队列需要可靠的消息中间件
- 会话状态缓存减少 DB 压力
- 后续可扩展为 Celery/ARQ 任务队列

### 4. 文件管理为什么用 Git？
- 天然支持版本历史、diff、分支
- committed/ 目录 = Git tracked
- drafts/ 目录 = .gitignore
- 用户确认入库 = git add + commit

### 5. 为什么 PostgreSQL 而不是继续用 SQLite？
- 并发写入：20+ Agent 同时写消息，SQLite 锁竞争严重
- JSON 查询：PostgreSQL 原生 JSONB 索引
- 全文搜索：PostgreSQL 内置 tsvector
- 开发环境仍可用 SQLite（SQLModel 兼容）

---

## 部署架构

### 开发环境
```
docker-compose up
  ├── backend (FastAPI + uvicorn, hot reload)
  ├── frontend (Vite dev server, HMR)
  ├── postgres (数据库)
  └── redis (缓存/消息)
```

### 生产环境
```
docker-compose -f docker-compose.prod.yml up
  ├── nginx (反向代理 + 静态文件)
  ├── backend (Gunicorn + uvicorn workers × N)
  ├── postgres (数据库)
  └── redis (缓存/消息)
```
