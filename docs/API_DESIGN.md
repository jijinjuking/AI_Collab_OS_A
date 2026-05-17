# AI-Collab-OS API 设计

## 基础信息

- Base URL: `/api/v1`
- 认证: Bearer JWT Token (Header: `Authorization: Bearer <token>`)
- 响应格式: JSON
- 错误格式: `{ "success": false, "error": { "code": "ERR_CODE", "message": "描述" } }`
- 成功格式: `{ "success": true, "data": {...} }`

---

## 1. 认证模块 `/api/v1/auth`

### POST /auth/register
注册新用户

**Request:**
```json
{
  "username": "string (3-50字符)",
  "email": "string (可选)",
  "password": "string (6-100字符)"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid", "username": "string", "role": "user" },
    "token": "jwt-string"
  }
}
```

### POST /auth/login
用户登录

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid", "username": "string", "role": "string" },
    "token": "jwt-string"
  }
}
```

### GET /auth/profile
获取当前用户信息（需认证）

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "role": "string",
    "settings": {},
    "created_at": "ISO8601"
  }
}
```

### PUT /auth/settings
更新用户设置（需认证）

**Request:**
```json
{
  "settings": {
    "default_provider": "openai",
    "default_model": "gpt-4o",
    "dark_mode": true
  }
}
```

---

## 2. 项目模块 `/api/v1/projects`

### GET /projects
获取用户的项目列表

**Query:** `?status=active&page=1&limit=20`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "string",
        "status": "active",
        "agent_count": 12,
        "created_at": "ISO8601",
        "updated_at": "ISO8601"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 20
  }
}
```

### POST /projects
创建项目

**Request:**
```json
{
  "name": "电商平台",
  "description": "全栈电商系统",
  "plan": "项目任务书内容...",
  "config": {
    "tech_stack": ["React", "FastAPI", "PostgreSQL"],
    "constraints": "移动端优先"
  }
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "电商平台",
    "status": "draft",
    "workspace_path": "/workspaces/uuid",
    "created_at": "ISO8601"
  }
}
```

### GET /projects/:id
获取项目详情

### PUT /projects/:id
更新项目信息

### PUT /projects/:id/plan
更新项目任务书

**Request:**
```json
{
  "plan": "更新后的任务书内容..."
}
```

### DELETE /projects/:id
删除项目（软删除，status → archived）

---

## 3. 角色模板模块 `/api/v1/roles`

### GET /roles
获取角色列表（系统预设 + 用户自定义）

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "key": "product_manager",
      "name": "产品经理",
      "icon": "fas fa-user-tie",
      "system_prompt": "你是一位高级产品经理...",
      "is_system": true,
      "default_model": "gpt-4o"
    },
    {
      "id": "uuid",
      "key": "custom-devops",
      "name": "DevOps 工程师",
      "is_system": false
    }
  ]
}
```

### POST /roles
创建自定义角色

**Request:**
```json
{
  "key": "custom-devops",
  "name": "DevOps 工程师",
  "icon": "fas fa-cloud",
  "system_prompt": "你是一位 DevOps 专家...",
  "skills": ["Docker", "K8s", "CI/CD"],
  "default_model": "claude-3-5-sonnet"
}
```

### PUT /roles/:id
更新自定义角色

### DELETE /roles/:id
删除自定义角色（仅限用户自定义）

---

## 4. Agent 实例模块 `/api/v1/projects/:project_id/agents`

### GET /projects/:project_id/agents
获取项目中的所有 Agent 实例

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "role_template_id": "uuid",
      "role_key": "frontend",
      "role_name": "前端工程师",
      "instance_name": "前端1号",
      "instance_index": 1,
      "status": "working",
      "provider": "openai",
      "model": "gpt-4o",
      "token_used": 15420,
      "created_at": "ISO8601"
    }
  ]
}
```

### POST /projects/:project_id/agents
创建 Agent 实例（拉人进项目）

**Request:**
```json
{
  "role_template_id": "uuid",
  "instance_name": "前端3号",
  "provider": "openai",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "api_key_id": "uuid",
  "system_prompt_override": "可选覆盖 prompt",
  "config": {
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

**Response 201:** 返回创建的 Agent 实例

### POST /projects/:project_id/agents/batch
批量创建 Agent（一次拉 5 个前端）

**Request:**
```json
{
  "role_template_id": "uuid",
  "count": 5,
  "provider": "openai",
  "model": "gpt-4o",
  "api_key_id": "uuid",
  "name_prefix": "前端"
}
```

**Response 201:** 返回创建的 5 个 Agent 实例数组

### PUT /projects/:project_id/agents/:agent_id
更新 Agent 配置

### DELETE /projects/:project_id/agents/:agent_id
移除 Agent（从项目中删除）

### POST /projects/:project_id/agents/:agent_id/chat
向 Agent 发送消息（用户 → Agent 对话）

**Request:**
```json
{
  "message": "请根据 PRD 设计首页组件",
  "context": {
    "include_plan": true,
    "include_pending_tasks": true
  }
}
```

**Response 200 (SSE stream):**
```
event: token
data: {"content": "好的"}

event: token
data: {"content": "，我来"}

event: done
data: {"message_id": "uuid", "token_count": 1520, "directives": []}
```

---

## 5. 工作流模块 `/api/v1/projects/:project_id/workflows`

### GET /projects/:project_id/workflows
获取项目的工作流列表

### POST /projects/:project_id/workflows
创建工作流

**Request:**
```json
{
  "name": "全栈开发流程",
  "type": "custom",
  "mode": "auto",
  "max_review_rounds": 3,
  "dag_config": {
    "nodes": [
      { "id": "n1", "agent_id": "uuid", "step_type": "execute", "label": "PM 写 PRD" },
      { "id": "n2", "agent_id": "uuid", "step_type": "discuss", "label": "架构师讨论", "discuss_with": "n3" },
      { "id": "n3", "agent_id": "uuid", "step_type": "discuss", "label": "架构师B讨论", "discuss_with": "n2" }
    ],
    "edges": [
      { "from": "n1", "to": "n2" },
      { "from": "n1", "to": "n3" }
    ]
  }
}
```

### POST /projects/:project_id/workflows/:workflow_id/start
启动工作流

**Response 200:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "uuid",
    "status": "running",
    "current_step": { "id": "n1", "label": "PM 写 PRD" }
  }
}
```

### POST /projects/:project_id/workflows/:workflow_id/pause
暂停工作流

### POST /projects/:project_id/workflows/:workflow_id/resume
恢复工作流

### POST /projects/:project_id/workflows/:workflow_id/stop
停止工作流

### POST /projects/:project_id/workflows/:workflow_id/step
手动推进一步（手动模式）

### GET /projects/:project_id/workflows/:workflow_id/status
获取工作流当前状态

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "running",
    "mode": "auto",
    "current_steps": [
      { "id": "n4", "agent_name": "前端1号", "status": "working", "started_at": "ISO8601" },
      { "id": "n5", "agent_name": "前端2号", "status": "working", "started_at": "ISO8601" }
    ],
    "completed_steps": 3,
    "total_steps": 12,
    "progress_percent": 25
  }
}
```

### POST /projects/:project_id/workflows/:workflow_id/intervene
用户介入（插入指令）

**Request:**
```json
{
  "target_agent_id": "uuid",
  "message": "方向不对，改用 Vue 而不是 React",
  "action": "redirect"
}
```

---

## 6. 消息模块 `/api/v1/projects/:project_id/messages`

### GET /projects/:project_id/messages
获取项目消息历史

**Query:** `?agent_id=uuid&type=handoff&from=ISO8601&to=ISO8601&page=1&limit=50`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "from_agent": { "id": "uuid", "name": "架构师A", "role_key": "architect" },
        "to_agent": { "id": "uuid", "name": "前端1号", "role_key": "frontend" },
        "message_type": "handoff",
        "role": "assistant",
        "content": "请实现以下组件...",
        "summary": "分配首页组件开发任务",
        "token_count": 850,
        "model_used": "gpt-4o",
        "created_at": "ISO8601"
      }
    ],
    "total": 156,
    "page": 1
  }
}
```

### GET /projects/:project_id/messages/stream
SSE 实时消息流（替代轮询）

```
event: message
data: {"id":"uuid","from_agent":{"name":"架构师"},"type":"handoff","content":"...","created_at":"ISO8601"}

event: status
data: {"agent_id":"uuid","status":"working"}

event: workflow
data: {"step_id":"n4","status":"completed"}
```

---

## 7. 文件模块 `/api/v1/projects/:project_id/files`

### GET /projects/:project_id/files/tree
获取文件树

**Response 200:**
```json
{
  "success": true,
  "data": {
    "tree": [
      {
        "name": "src",
        "type": "directory",
        "children": [
          { "name": "App.tsx", "type": "file", "status": "committed", "language": "typescript", "size": 2048 },
          { "name": "index.css", "type": "file", "status": "draft", "language": "css", "size": 512 }
        ]
      }
    ]
  }
}
```

### GET /projects/:project_id/files/content
获取文件内容

**Query:** `?path=src/App.tsx&version=latest`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "path": "src/App.tsx",
    "content": "import React from 'react'...",
    "language": "typescript",
    "status": "draft",
    "version": 2,
    "created_by": { "id": "uuid", "name": "前端1号" },
    "updated_at": "ISO8601"
  }
}
```

### POST /projects/:project_id/files
创建/更新文件

**Request:**
```json
{
  "path": "src/components/Header.tsx",
  "content": "import React from 'react'...",
  "language": "typescript",
  "status": "draft",
  "created_by_agent_id": "uuid"
}
```

### POST /projects/:project_id/files/commit
将草稿文件提升为正式代码

**Request:**
```json
{
  "file_paths": ["src/App.tsx", "src/components/Header.tsx"],
  "commit_message": "feat: 完成首页组件开发"
}
```

### DELETE /projects/:project_id/files
删除文件

**Request:**
```json
{
  "path": "src/temp/draft.tsx"
}
```

### GET /projects/:project_id/files/download
打包下载项目（zip）

**Response:** `Content-Type: application/zip`

---

## 8. API Key 管理 `/api/v1/api-keys`

### GET /api-keys
获取用户的 API Key 列表（脱敏显示）

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "provider": "openai",
      "name": "我的 OpenAI Key",
      "base_url": "https://api.openai.com/v1",
      "key_preview": "sk-...7x2f",
      "is_default": true,
      "created_at": "ISO8601"
    }
  ]
}
```

### POST /api-keys
添加 API Key

**Request:**
```json
{
  "provider": "openai",
  "name": "我的 OpenAI Key",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-xxxxxxxx",
  "is_default": true
}
```

### DELETE /api-keys/:id
删除 API Key

---

## 9. 沙箱执行 `/api/v1/projects/:project_id/sandbox`

### POST /projects/:project_id/sandbox/create
创建项目沙箱容器

**Request:**
```json
{
  "image": "node:20-slim",
  "resource_limits": {
    "cpu": "1.0",
    "memory": "512m",
    "timeout": 300
  }
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "container_id": "abc123",
    "status": "running",
    "image": "node:20-slim"
  }
}
```

### POST /projects/:project_id/sandbox/exec
在沙箱中执行命令

**Request:**
```json
{
  "session_id": "uuid",
  "command": "npm test",
  "agent_id": "uuid",
  "timeout": 60
}
```

**Response 200 (SSE stream):**
```
event: stdout
data: {"line": "PASS src/App.test.tsx"}

event: stdout
data: {"line": "Tests: 3 passed, 3 total"}

event: done
data: {"exit_code": 0, "duration_ms": 4520}
```

### POST /projects/:project_id/sandbox/destroy
销毁沙箱容器

**Request:**
```json
{
  "session_id": "uuid"
}
```

### GET /projects/:project_id/sandbox/status
获取沙箱状态

---

## 10. 文件锁 `/api/v1/projects/:project_id/files/locks`

### GET /projects/:project_id/files/locks
获取当前所有文件锁

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "file_path": "src/App.tsx",
      "locked_by": { "id": "uuid", "name": "前端1号", "role_key": "frontend" },
      "lock_type": "exclusive",
      "acquired_at": "ISO8601",
      "expires_at": "ISO8601"
    }
  ]
}
```

### POST /projects/:project_id/files/locks/acquire
获取文件锁

**Request:**
```json
{
  "file_path": "src/App.tsx",
  "agent_id": "uuid",
  "lock_type": "exclusive",
  "ttl_seconds": 300
}
```

**Response 200:** 成功获取锁
**Response 409:** 文件已被其他 Agent 锁定
```json
{
  "success": false,
  "error": {
    "code": "FILE_LOCKED",
    "message": "文件已被 前端2号 锁定",
    "locked_by": { "id": "uuid", "name": "前端2号" },
    "expires_at": "ISO8601"
  }
}
```

### POST /projects/:project_id/files/locks/release
释放文件锁

**Request:**
```json
{
  "file_path": "src/App.tsx",
  "agent_id": "uuid"
}
```

### POST /projects/:project_id/files/locks/force-release
强制释放锁（用户手动解锁死锁）

---

## 11. 活动日志 `/api/v1/projects/:project_id/logs`

### GET /projects/:project_id/logs
获取活动日志

**Query:** `?actor_type=agent&action=handoff&from=ISO8601&limit=100`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "actor_type": "agent",
        "actor_name": "架构师A",
        "action": "handoff",
        "detail": { "to": "前端1号", "summary": "分配任务" },
        "created_at": "ISO8601"
      }
    ]
  }
}
```

---

## 10. WebSocket 协议 `/ws`

### 连接
```
ws://host/ws?token=<jwt>
```

### 客户端 → 服务端消息

**订阅项目频道:**
```json
{ "type": "subscribe", "project_id": "uuid" }
```

**用户发送消息给 Agent:**
```json
{
  "type": "chat",
  "project_id": "uuid",
  "agent_id": "uuid",
  "content": "请开始工作"
}
```

**用户介入工作流:**
```json
{
  "type": "intervene",
  "project_id": "uuid",
  "workflow_id": "uuid",
  "target_agent_id": "uuid",
  "content": "改方向"
}
```

### 服务端 → 客户端消息

**Agent 对话消息（实时流）:**
```json
{
  "type": "agent:message",
  "project_id": "uuid",
  "data": {
    "message_id": "uuid",
    "from_agent": { "id": "uuid", "name": "架构师A", "role_key": "architect" },
    "to_agent": { "id": "uuid", "name": "前端1号", "role_key": "frontend" },
    "message_type": "handoff",
    "content": "请实现...",
    "summary": "分配任务",
    "created_at": "ISO8601"
  }
}
```

**Agent 状态变更:**
```json
{
  "type": "agent:status",
  "project_id": "uuid",
  "data": {
    "agent_id": "uuid",
    "agent_name": "前端1号",
    "status": "working",
    "current_task": "实现 Header 组件"
  }
}
```

**工作流进度:**
```json
{
  "type": "workflow:progress",
  "project_id": "uuid",
  "data": {
    "workflow_id": "uuid",
    "step_id": "n4",
    "step_label": "前端1号开发",
    "status": "completed",
    "progress_percent": 42
  }
}
```

**Token 流式输出:**
```json
{
  "type": "agent:token",
  "project_id": "uuid",
  "data": {
    "agent_id": "uuid",
    "token": "好的，",
    "is_final": false
  }
}
```

**系统通知:**
```json
{
  "type": "system:notification",
  "data": {
    "level": "warning",
    "message": "审查循环已达 3 轮上限",
    "action_required": true
  }
}
```

---

## 错误码

| Code | HTTP | 说明 |
|------|------|------|
| AUTH_REQUIRED | 401 | 未提供 Token |
| AUTH_INVALID | 401 | Token 无效或过期 |
| AUTH_FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| VALIDATION_ERROR | 422 | 请求参数校验失败 |
| LLM_ERROR | 502 | LLM API 调用失败 |
| LLM_TIMEOUT | 504 | LLM API 超时 |
| LLM_QUOTA | 429 | Token 预算耗尽 |
| WORKFLOW_CONFLICT | 409 | 工作流状态冲突 |
| DB_ERROR | 500 | 数据库错误 |

---

## 设计决策

1. **SSE + WebSocket 双通道** — REST API 用 SSE 做单 Agent 对话流式输出；WebSocket 做全局实时广播（多 Agent 消息、状态变更、工作流进度）
2. **Agent 对话走 REST** — 用户主动发消息用 POST + SSE 响应，保证请求-响应语义清晰
3. **批量创建** — 支持一次拉 N 个同角色 Agent，减少前端交互次数
4. **文件版本化** — 通过 version 参数支持历史版本查看，但不做完整 Git 暴露
5. **消息分页** — 默认 50 条/页，支持按类型/时间/Agent 过滤
6. **API Key 脱敏** — 列表只返回 preview，完整 key 仅在创建时可见
