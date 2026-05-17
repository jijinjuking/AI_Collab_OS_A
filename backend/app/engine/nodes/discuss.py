"""Discuss node: two agents exchange ideas on a topic."""

from typing import Any

from loguru import logger

from app.engine.state import AgentOutput, WorkflowState


async def run_discuss_node(
    state: WorkflowState, node_id: str, agent_id: str, config: dict[str, Any]
) -> dict:
    """Discuss node logic.

    Two agents take turns discussing. This node represents one agent's turn.
    The paired agent's node handles the other side.
    Context from previous outputs feeds the discussion.
    """
    from app.core.events import event_bus
    from app.db.session import async_session_factory
    from app.services.agent_service import AgentService
    from app.schemas.agent import AgentChatRequest

    project_id = state["project_id"]
    task = state["task_description"]
    previous_outputs = state.get("outputs", [])

    # Build discussion prompt
    discuss_with = config.get("discuss_with", "")
    prompt_parts = [
        f"任务背景:\n{task}",
        "\n你正在与团队成员讨论方案。请基于以下上下文给出你的观点和建议。",
    ]

    if previous_outputs:
        prompt_parts.append("\n讨论历史:")
        for out in previous_outputs[-4:]:
            prompt_parts.append(f"\n[{out['agent_name']}]:\n{out['content'][:2000]}")

    prompt_parts.append("\n请给出你的分析和建议，保持简洁专业。")
    message = "\n".join(prompt_parts)

    await event_bus.publish_agent_status(project_id, agent_id, "working")

    async with async_session_factory() as session:
        service = AgentService(session)
        agent = await service.get_agent(agent_id)

        request = AgentChatRequest(message=message, stream=False)
        response = await service.chat(agent, request)
        await session.commit()

    output = AgentOutput(
        agent_id=agent_id,
        agent_name=config.get("label", node_id),
        content=response.content,
        token_count=response.total_tokens,
        model_used=response.model,
    )

    await event_bus.publish_agent_message(
        project_id=project_id,
        from_agent=agent_id,
        to_agent=None,
        message_type="discuss",
        content=response.content[:500],
        node_id=node_id,
        agent_name=config.get("label", node_id),
    )

    await event_bus.publish_agent_status(project_id, agent_id, "idle")

    logger.info(f"Discuss node {node_id}: agent={agent_id}, tokens={response.total_tokens}")

    return {
        "outputs": state.get("outputs", []) + [output],
        "current_step_id": node_id,
        "current_step_type": "discuss",
    }
