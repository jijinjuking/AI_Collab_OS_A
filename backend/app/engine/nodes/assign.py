"""Assign node: architect distributes tasks to multiple agents."""

from typing import Any

from loguru import logger

from app.engine.state import AgentOutput, WorkflowState


async def run_assign_node(
    state: WorkflowState, node_id: str, agent_id: str, config: dict[str, Any]
) -> dict:
    """Assign node logic.

    The architect agent analyzes the task and produces a task breakdown
    that will be consumed by downstream execute nodes.
    """
    from app.core.events import event_bus
    from app.db.session import async_session_factory
    from app.services.agent_service import AgentService
    from app.schemas.agent import AgentChatRequest

    project_id = state["project_id"]
    task = state["task_description"]
    previous_outputs = state.get("outputs", [])
    assign_to = config.get("assign_to", [])

    # Build assignment prompt
    prompt_parts = [
        f"任务描述:\n{task}",
    ]

    if previous_outputs:
        prompt_parts.append("\n前序讨论/分析结果:")
        for out in previous_outputs[-3:]:
            prompt_parts.append(f"\n[{out['agent_name']}]:\n{out['content'][:2000]}")

    prompt_parts.append(
        f"\n请将任务分解为 {len(assign_to)} 个子任务，分配给下游 Agent。"
        "\n输出格式:\n"
        "## 子任务 1\n目标: ...\n要求: ...\n\n"
        "## 子任务 2\n目标: ...\n要求: ...\n"
    )

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
        message_type="assign",
        content=response.content[:500],
        node_id=node_id,
        assign_to=assign_to,
        agent_name=config.get("label", node_id),
    )

    await event_bus.publish_agent_status(project_id, agent_id, "idle")

    logger.info(f"Assign node {node_id}: distributed to {len(assign_to)} targets")

    return {
        "outputs": state.get("outputs", []) + [output],
        "current_step_id": node_id,
        "current_step_type": "assign",
    }
