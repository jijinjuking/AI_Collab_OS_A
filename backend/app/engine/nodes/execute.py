"""Execute node: an agent performs a task and produces output."""

from typing import Any

from loguru import logger

from app.engine.state import AgentOutput, WorkflowState


async def run_execute_node(
    state: WorkflowState, node_id: str, agent_id: str, config: dict[str, Any]
) -> dict:
    """Execute node logic.

    The agent receives the task description (or previous outputs as context)
    and produces content (code, docs, plans, etc.).
    """
    from app.core.events import event_bus
    from app.db.session import async_session_factory
    from app.services.agent_service import AgentService
    from app.schemas.agent import AgentChatRequest

    project_id = state["project_id"]
    task = state["task_description"]
    previous_outputs = state.get("outputs", [])

    # Build context from previous outputs
    context_parts = [f"任务描述:\n{task}"]
    if previous_outputs:
        context_parts.append("\n前序 Agent 产出:")
        for out in previous_outputs[-5:]:  # Last 5 outputs for context
            context_parts.append(f"\n[{out['agent_name']}]:\n{out['content'][:2000]}")

    message = "\n".join(context_parts)

    # Notify: agent starts working
    await event_bus.publish_agent_status(project_id, agent_id, "working")

    async with async_session_factory() as session:
        service = AgentService(session)
        agent = await service.get_agent(agent_id)

        request = AgentChatRequest(message=message, stream=False)
        response = await service.chat(agent, request)
        await session.commit()

    # Build output
    output = AgentOutput(
        agent_id=agent_id,
        agent_name=config.get("label", node_id),
        content=response.content,
        token_count=response.total_tokens,
        model_used=response.model,
    )

    # Notify: agent message produced
    await event_bus.publish_agent_message(
        project_id=project_id,
        from_agent=agent_id,
        to_agent=None,
        message_type="execute",
        content=response.content[:500],
        node_id=node_id,
        agent_name=config.get("label", node_id),
    )

    await event_bus.publish_agent_status(project_id, agent_id, "idle")

    logger.info(f"Execute node {node_id}: agent={agent_id}, tokens={response.total_tokens}")

    return {
        "outputs": state.get("outputs", []) + [output],
        "current_step_id": node_id,
        "current_step_type": "execute",
    }
