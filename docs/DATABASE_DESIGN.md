# AI-Collab-OS 数据库设计

## 技术选型

- ORM: SQLModel (SQLAlchemy + Pydantic 合体)
- 开发环境: SQLite
- 生产环境: PostgreSQL
- 迁移工具: Alembic

---

## 实体关系图 (ER)

```
User 1──N Project
Project 1──N ProjectAgent
Project 1──N Workflow
Project 1──N ProjectFile
ProjectAgent N──1 RoleTemplate
ProjectAgent 1──N AgentMessage
Workflow 1──N WorkflowStep
Workflow 1──N AgentMessage
User 1──N RoleTemplate (自定义角色)
User 1──N ApiKeyConfig
```

---

## 表设计

### 1. users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| role | VARCHAR(20) | DEFAULT 'user' | admin/user |
| settings | JSON | | 用户偏好设置 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

### 2. projects — 项目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id | 所属用户 |
| name | VARCHAR(100) | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| plan | TEXT | | 项目任务书 |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/active/paused/completed/archived |
| config | JSON | | 项目配置（技术栈、约束等） |
| workspace_path | VARCHAR(500) | | 工作区路径 |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

### 3. role_templates — 角色模板表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id, NULLABLE | NULL=系统预设, 非NULL=用户自定义 |
| key | VARCHAR(50) | NOT NULL | 角色标识 (product_manager, architect...) |
| name | VARCHAR(50) | NOT NULL | 显示名称 |
| icon | VARCHAR(50) | | 图标 class |
| system_prompt | TEXT | NOT NULL | System Prompt 模板 |
| skills | JSON | | 角色技能描述 |
| default_model | VARCHAR(100) | | 默认模型 |
| is_system | BOOLEAN | DEFAULT false | 是否系统预设 |
| created_at | TIMESTAMP | NOT NULL | |

**唯一约束:** (user_id, key) — 同一用户下角色 key 不重复

### 4. project_agents — 项目中的 Agent 实例

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| role_template_id | UUID | FK → role_templates.id | 角色模板 |
| instance_name | VARCHAR(100) | NOT NULL | 实例名称（前端1号、架构师A） |
| instance_index | INT | NOT NULL | 实例序号 |
| status | VARCHAR(20) | DEFAULT 'idle' | idle/working/paused/error |
| provider | VARCHAR(50) | | openai/anthropic/ollama |
| base_url | VARCHAR(500) | | API 地址 |
| model | VARCHAR(100) | | 模型名称 |
| api_key_id | UUID | FK → api_keys.id, NULLABLE | 关联的 API Key |
| system_prompt_override | TEXT | | 覆盖角色默认 prompt |
| config | JSON | | Agent 级别配置（temperature 等） |
| token_used | BIGINT | DEFAULT 0 | 累计 Token 消耗 |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**唯一约束:** (project_id, role_template_id, instance_index)

### 5. workflows — 工作流表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| name | VARCHAR(100) | | 工作流名称 |
| type | VARCHAR(30) | NOT NULL | full/frontend/backend/custom |
| status | VARCHAR(20) | DEFAULT 'pending' | pending/running/paused/completed/failed |
| dag_config | JSON | NOT NULL | DAG 配置（节点、边、条件） |
| current_step_id | UUID | NULLABLE | 当前执行步骤 |
| mode | VARCHAR(10) | DEFAULT 'manual' | auto/manual |
| max_review_rounds | INT | DEFAULT 3 | 最大审查轮次 |
| started_at | TIMESTAMP | | |
| completed_at | TIMESTAMP | | |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

### 6. workflow_steps — 工作流步骤表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| workflow_id | UUID | FK → workflows.id | 所属工作流 |
| agent_id | UUID | FK → project_agents.id | 执行 Agent |
| step_type | VARCHAR(30) | NOT NULL | execute/review/discuss/assign |
| step_order | INT | NOT NULL | 执行顺序 |
| depends_on | JSON | | 依赖的步骤 ID 列表 |
| status | VARCHAR(20) | DEFAULT 'pending' | pending/running/completed/failed/skipped |
| input_data | JSON | | 输入数据 |
| output_data | JSON | | 输出数据 |
| review_round | INT | DEFAULT 0 | 当前审查轮次 |
| started_at | TIMESTAMP | | |
| completed_at | TIMESTAMP | | |
| error_message | TEXT | | 错误信息 |

### 7. agent_messages — Agent 消息表（核心通信记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| workflow_id | UUID | FK → workflows.id, NULLABLE | 关联工作流 |
| from_agent_id | UUID | FK → project_agents.id, NULLABLE | 发送方（NULL=用户/系统） |
| to_agent_id | UUID | FK → project_agents.id, NULLABLE | 接收方（NULL=广播） |
| message_type | VARCHAR(20) | NOT NULL | chat/handoff/issue/review/discuss/system |
| role | VARCHAR(20) | NOT NULL | user/assistant/system |
| content | TEXT | NOT NULL | 消息内容 |
| summary | VARCHAR(500) | | 摘要 |
| metadata | JSON | | 附加信息（severity, verdict, score 等） |
| token_count | INT | | 消息 Token 数 |
| model_used | VARCHAR(100) | | 使用的模型 |
| created_at | TIMESTAMP | NOT NULL | |

**索引:** (project_id, created_at), (workflow_id), (from_agent_id), (to_agent_id)

### 8. project_files — 项目文件表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| file_path | VARCHAR(500) | NOT NULL | 文件路径（相对项目根） |
| file_type | VARCHAR(20) | NOT NULL | source/draft/doc/config/test |
| content | TEXT | | 文件内容 |
| language | VARCHAR(30) | | 编程语言 |
| created_by_agent_id | UUID | FK → project_agents.id, NULLABLE | 创建者 Agent |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/committed/deleted |
| version | INT | DEFAULT 1 | 版本号 |
| git_commit_hash | VARCHAR(40) | | Git commit SHA |
| size_bytes | INT | | 文件大小 |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**唯一约束:** (project_id, file_path, version)

### 9. api_keys — API Key 管理表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id | 所属用户 |
| provider | VARCHAR(50) | NOT NULL | openai/anthropic/ollama/custom |
| name | VARCHAR(100) | NOT NULL | 显示名称 |
| base_url | VARCHAR(500) | | API 地址 |
| encrypted_key | TEXT | NOT NULL | AES 加密的 API Key |
| is_default | BOOLEAN | DEFAULT false | 是否默认 |
| created_at | TIMESTAMP | NOT NULL | |

### 10. file_locks — 文件锁表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| file_path | VARCHAR(500) | NOT NULL | 被锁定的文件路径 |
| locked_by_agent_id | UUID | FK → project_agents.id | 锁定者 Agent |
| lock_type | VARCHAR(20) | DEFAULT 'exclusive' | exclusive/shared |
| acquired_at | TIMESTAMP | NOT NULL | 获取锁时间 |
| expires_at | TIMESTAMP | | 过期时间（防死锁） |
| released_at | TIMESTAMP | | 释放时间 |

**唯一约束:** (project_id, file_path, released_at IS NULL) — 同一文件同时只有一把有效锁

### 11. sandbox_sessions — 沙箱执行会话表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| container_id | VARCHAR(100) | | Docker 容器 ID |
| status | VARCHAR(20) | DEFAULT 'created' | created/running/stopped/destroyed |
| image | VARCHAR(200) | NOT NULL | Docker 镜像名 |
| resource_limits | JSON | | CPU/内存/磁盘限制 |
| created_at | TIMESTAMP | NOT NULL | |
| destroyed_at | TIMESTAMP | | |

### 12. sandbox_executions — 沙箱执行记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| session_id | UUID | FK → sandbox_sessions.id | 所属沙箱会话 |
| agent_id | UUID | FK → project_agents.id | 发起执行的 Agent |
| command | TEXT | NOT NULL | 执行的命令 |
| stdout | TEXT | | 标准输出 |
| stderr | TEXT | | 标准错误 |
| exit_code | INT | | 退出码 |
| duration_ms | INT | | 执行耗时(毫秒) |
| status | VARCHAR(20) | DEFAULT 'pending' | pending/running/completed/timeout/error |
| created_at | TIMESTAMP | NOT NULL | |
| completed_at | TIMESTAMP | | |

### 13. activity_logs — 活动日志表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| project_id | UUID | FK → projects.id | 所属项目 |
| actor_type | VARCHAR(20) | NOT NULL | user/agent/system |
| actor_id | UUID | | 操作者 ID |
| action | VARCHAR(50) | NOT NULL | 动作类型 |
| detail | JSON | | 详细信息 |
| created_at | TIMESTAMP | NOT NULL | |

**索引:** (project_id, created_at DESC)

---

## DAG 配置结构 (workflows.dag_config)

```json
{
  "nodes": [
    {
      "id": "node_1",
      "agent_id": "uuid-of-pm",
      "step_type": "execute",
      "label": "产品经理编写 PRD"
    },
    {
      "id": "node_2a",
      "agent_id": "uuid-of-architect-a",
      "step_type": "discuss",
      "label": "架构师A 讨论",
      "discuss_with": "node_2b"
    },
    {
      "id": "node_2b",
      "agent_id": "uuid-of-architect-b",
      "step_type": "discuss",
      "label": "架构师B 讨论",
      "discuss_with": "node_2a"
    },
    {
      "id": "node_3",
      "agent_id": "uuid-of-architect-a",
      "step_type": "assign",
      "label": "架构师分配任务",
      "assign_to": ["node_4a", "node_4b", "node_5a", "node_5b"]
    },
    {
      "id": "node_4a",
      "agent_id": "uuid-of-frontend-1",
      "step_type": "execute",
      "label": "前端1号开发"
    },
    {
      "id": "node_4b",
      "agent_id": "uuid-of-frontend-2",
      "step_type": "execute",
      "label": "前端2号开发"
    },
    {
      "id": "node_6",
      "agent_id": "uuid-of-reviewer",
      "step_type": "review",
      "label": "代码审查",
      "review_targets": ["node_4a", "node_4b"]
    }
  ],
  "edges": [
    {"from": "node_1", "to": "node_2a"},
    {"from": "node_1", "to": "node_2b"},
    {"from": "node_2a", "to": "node_3"},
    {"from": "node_2b", "to": "node_3"},
    {"from": "node_3", "to": "node_4a"},
    {"from": "node_3", "to": "node_4b"},
    {"from": "node_4a", "to": "node_6"},
    {"from": "node_4b", "to": "node_6"}
  ]
}
```

---

## 设计决策

1. **UUID 主键** — 分布式友好，前端可预生成 ID
2. **JSON 字段** — dag_config/settings/metadata 用 JSON 存储灵活结构
3. **软删除** — 文件用 status='deleted' 而非物理删除
4. **消息不分表** — 单表 agent_messages 通过索引满足查询，避免过早优化
5. **API Key 加密** — AES-256 加密存储，运行时解密
6. **版本化文件** — project_files 通过 version 字段支持历史版本
7. **Token 统计** — agent 级别累计 + message 级别明细，双重追踪
