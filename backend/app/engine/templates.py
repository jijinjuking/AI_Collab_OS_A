"""Workflow template library: preset DAG configurations for common development patterns.

Templates define the agent roles, node types, and edge connections
for typical multi-agent collaboration workflows.
"""

from typing import Any


def get_template(template_key: str) -> dict[str, Any] | None:
    """Get a workflow template by key."""
    return TEMPLATES.get(template_key)


def list_templates() -> list[dict[str, str]]:
    """List all available workflow templates."""
    return [
        {"key": k, "name": v["name"], "description": v["description"], "type": v["type"]}
        for k, v in TEMPLATES.items()
    ]


TEMPLATES: dict[str, dict[str, Any]] = {
    "fullstack": {
        "name": "全栈开发流程",
        "description": "PM需求分析 → 架构师设计 → 前后端并行开发 → 审查员Review",
        "type": "full",
        "dag_config": {
            "nodes": [
                {"id": "pm", "type": "execute", "agent_role": "pm", "label": "产品经理"},
                {"id": "architect", "type": "assign", "agent_role": "architect", "label": "架构师", "assign_to": ["frontend", "backend"]},
                {"id": "frontend", "type": "execute", "agent_role": "frontend", "label": "前端工程师"},
                {"id": "backend", "type": "execute", "agent_role": "backend", "label": "后端工程师"},
                {"id": "reviewer", "type": "review", "agent_role": "reviewer", "label": "代码审查员"},
            ],
            "edges": [
                {"from": "pm", "to": "architect"},
                {"from": "architect", "to": "frontend"},
                {"from": "architect", "to": "backend"},
                {"from": "frontend", "to": "reviewer"},
                {"from": "backend", "to": "reviewer"},
            ],
        },
    },
    "frontend_only": {
        "name": "前端开发流程",
        "description": "PM需求 → 前端开发 → UI审查 → 迭代优化",
        "type": "frontend",
        "dag_config": {
            "nodes": [
                {"id": "pm", "type": "execute", "agent_role": "pm", "label": "产品经理"},
                {"id": "frontend", "type": "execute", "agent_role": "frontend", "label": "前端工程师"},
                {"id": "reviewer", "type": "review", "agent_role": "reviewer", "label": "UI审查员"},
            ],
            "edges": [
                {"from": "pm", "to": "frontend"},
                {"from": "frontend", "to": "reviewer"},
            ],
        },
    },
    "backend_only": {
        "name": "后端开发流程",
        "description": "需求分析 → API设计 → 后端实现 → 代码审查",
        "type": "backend",
        "dag_config": {
            "nodes": [
                {"id": "pm", "type": "execute", "agent_role": "pm", "label": "产品经理"},
                {"id": "architect", "type": "execute", "agent_role": "architect", "label": "架构师"},
                {"id": "backend", "type": "execute", "agent_role": "backend", "label": "后端工程师"},
                {"id": "reviewer", "type": "review", "agent_role": "reviewer", "label": "代码审查员"},
            ],
            "edges": [
                {"from": "pm", "to": "architect"},
                {"from": "architect", "to": "backend"},
                {"from": "backend", "to": "reviewer"},
            ],
        },
    },
    "code_review": {
        "name": "代码审查流程",
        "description": "提交代码 → 多角度审查 → 讨论 → 最终决定",
        "type": "custom",
        "dag_config": {
            "nodes": [
                {"id": "security_review", "type": "review", "agent_role": "reviewer", "label": "安全审查"},
                {"id": "quality_review", "type": "review", "agent_role": "reviewer", "label": "质量审查"},
                {"id": "discuss", "type": "discuss", "agent_role": "architect", "label": "讨论决策"},
            ],
            "edges": [
                {"from": "security_review", "to": "discuss"},
                {"from": "quality_review", "to": "discuss"},
            ],
        },
    },
    "refactor": {
        "name": "重构流程",
        "description": "分析现有代码 → 设计重构方案 → 实施 → 验证",
        "type": "custom",
        "dag_config": {
            "nodes": [
                {"id": "analyze", "type": "execute", "agent_role": "architect", "label": "代码分析"},
                {"id": "plan", "type": "execute", "agent_role": "architect", "label": "重构方案"},
                {"id": "implement", "type": "execute", "agent_role": "backend", "label": "实施重构"},
                {"id": "test", "type": "execute", "agent_role": "tester", "label": "测试验证"},
                {"id": "review", "type": "review", "agent_role": "reviewer", "label": "最终审查"},
            ],
            "edges": [
                {"from": "analyze", "to": "plan"},
                {"from": "plan", "to": "implement"},
                {"from": "implement", "to": "test"},
                {"from": "test", "to": "review"},
            ],
        },
    },
    "brainstorm": {
        "name": "头脑风暴",
        "description": "多角色讨论方案 → 架构师总结 → 输出决策",
        "type": "custom",
        "dag_config": {
            "nodes": [
                {"id": "discuss_pm", "type": "discuss", "agent_role": "pm", "label": "PM视角"},
                {"id": "discuss_arch", "type": "discuss", "agent_role": "architect", "label": "架构视角"},
                {"id": "discuss_dev", "type": "discuss", "agent_role": "backend", "label": "开发视角"},
                {"id": "summary", "type": "execute", "agent_role": "architect", "label": "总结决策"},
            ],
            "edges": [
                {"from": "discuss_pm", "to": "summary"},
                {"from": "discuss_arch", "to": "summary"},
                {"from": "discuss_dev", "to": "summary"},
            ],
        },
    },
}
