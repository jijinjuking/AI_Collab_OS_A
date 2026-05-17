# AI-Collab-OS

多 Agent 协作开发平台 — 基于 LangGraph 的智能工作流引擎，支持多角色 AI Agent 协同完成软件开发任务。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy · SQLModel · LangGraph |
| 前端 | React 18 · TypeScript · Vite · Zustand · React Flow |
| 数据库 | PostgreSQL 16 (生产) / SQLite (开发) |
| 缓存 | Redis 7 |
| 部署 | Docker · Docker Compose · Nginx |

## 快速开始

### 前置要求

- Docker & Docker Compose V2
- (可选) Node.js 20+、Python 3.11+ 用于本地开发

### 一键启动

```bash
# 1. 克隆项目
git clone <repo-url> && cd ai-collab-platform

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 SECRET_KEY、JWT_SECRET_KEY、LLM API Key 等

# 3. 启动
chmod +x start.sh
./start.sh up
```

启动后访问：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs (仅开发环境)

### 常用命令

```bash
./start.sh up        # 启动
./start.sh down      # 停止
./start.sh restart   # 重启
./start.sh logs      # 查看日志
./start.sh status    # 健康检查
./start.sh migrate   # 数据库迁移
./start.sh clean     # 清理所有数据
```

## 本地开发

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 启动 (需要本地 Redis)
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## 项目结构

```
ai-collab-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # 路由层 (auth, agents, workflows, api_keys, monitoring)
│   │   ├── core/         # 中间件、Redis、WebSocket、速率限制
│   │   ├── db/           # 数据模型、会话管理、种子数据
│   │   ├── engine/       # LangGraph 工作流引擎 (nodes, runner, state)
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── services/     # 业务逻辑层
│   │   └── main.py       # FastAPI 入口
│   ├── alembic/          # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios 接口层
│   │   ├── components/   # 通用组件
│   │   ├── hooks/        # WebSocket 等 hooks
│   │   ├── pages/        # 页面组件
│   │   ├── store/        # Zustand 状态管理
│   │   └── styles/       # CSS 样式
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── start.sh
└── README.md
```

## API 概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | /api/v1/auth | 注册、登录、JWT |
| 项目 | /api/v1/projects | 项目 CRUD |
| Agent | /api/v1/agents | Agent 配置管理 |
| 工作流 | /api/v1/workflows | DAG 工作流管理与执行 |
| 文件 | /api/v1/files | 工作区文件管理 |
| API Key | /api/v1/api-keys | API Key 创建/撤销/删除 |
| 模板 | /api/v1/templates | 角色模板 |
| 监控 | /health, /metrics | 健康检查与系统指标 |
| WebSocket | /ws/{project_id} | 实时消息推送 |

## 环境变量

参见 [.env.example](.env.example) 获取完整配置项说明。

关键配置：
- `SECRET_KEY` / `JWT_SECRET_KEY` — 必须修改为随机字符串
- `DATABASE_URL` — 生产环境使用 PostgreSQL
- `REDIS_URL` — Redis 连接地址
- `OPENAI_API_KEY` — LLM 提供商密钥

## 健康检查

```bash
# 基础检查 (用于负载均衡)
curl http://localhost:8000/health

# 详细检查 (DB + Redis + 运行时间)
curl http://localhost:8000/health/detailed

# 系统指标 (连接池、WebSocket)
curl http://localhost:8000/metrics
```

## License

MIT
