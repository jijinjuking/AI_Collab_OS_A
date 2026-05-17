"""Review node: an agent reviews previous outputs and gives verdict."""

from typing import Any

from loguru import logger

from app.engine.state import AgentOutput, WorkflowState


async def run_review_node(
    state: WorkflowState, node_id: str, agent_id: str, config: dict[str, Any]
) -> dict:
    """Review node logic.

    The reviewer examines previous outputs and decides:
    - pass: work is acceptable, proceed
    - revise: needs changes, loop back to target
    - reject: fundamentally wrong (rare, escalates)
    """
    from app.core.events import event_bus
    from app.db.session import async_session_factory
    from app.services.agent_service import AgentService
    from app.schemas.agent import AgentChatRequest

    project_id = state["project_id"]
    previous_outputs = state.get("outputs", [])
    review_round = state.get("review_round", 0) + 1
    max_rounds = state.get("max_review_rounds", 3)

    # Build review prompt
    review_targets = config.get("review_targets", [])
    outputs_to_review = previous_outputs[-3:]  # Review last 3 outputs

    prompt_parts = [
        "你是代码审查员。请审查以下产出并给出评审意见。",
        f"\n当前审查轮次: {review_round}/{max_rounds}",
        "\n待审查内容:",
    ]

    for out in outputs_to_review:
        prompt_parts.append(f"\n[{out['agent_name']}]:\n{out['content'][:3000]}")

    prompt_parts.append(
        "\n\n请按以下格式回复:\n"
        "VERDICT: pass 或 revise\n"
        "FEEDBACK: 你的具体反馈意见\n"
        "SCORE: 1-10 分"
    )

    message = "\n".join(prompt_parts)

    await event_bus.publish_agent_status(project_id, agent_id, "working")

    async with async_session_factory() as session:
        service = AgentService(session)
        agent = await service.get_agent(agent_id)

        request = AgentChatRequest(message=message, stream=False)
        response = await service.chat(agent, request)
        await session.commit()

    # Parse verdict from response
    content = response.content
    verdict = "pass"  # Default to pass
    feedback = content

    content_upper = content.upper()
    if "VERDICT: REVISE" in content_upper or "VERDICT:REVISE" in content_upper:
        verdict = "revise"
    elif "VERDICT: REJECT" in content_upper or "VERDICT:REJECT" in content_upper:
        verdict = "reject"

    # If max rounds reached, force pass
    if review_round >= max_rounds and verdict != "pass":
        logger.warning(
            f"Review node {node_id}: max rounds ({max_rounds}) reached, forcing pass"
        )
        verdict = "pass"
        feedback += f"\n[系统: 已达最大审查轮次 {max_rounds}，自动通过]"

    output = AgentOutput(
        agent_id=agent_id,
        agent_name=config.get("label", node_id),
        content=content,
        token_count=response.total_tokens,
        model_used=response.model,
    )

    await event_bus.publish_agent_message(
        project_id=project_id,
        from_agent=agent_id,
        to_agent=None,
        message_type="review",
        content=content[:500],
        node_id=node_id,
        verdict=verdict,
        review_round=review_round,
        agent_name=config.get("label", node_id),
    )

    await event_bus.publish_agent_status(project_id, agent_id, "idle")

    logger.info(
        f"Review node {node_id}: verdict={verdict}, round={review_round}/{max_rounds}"
    )

    return {
        "outputs": state.get("outputs", []) + [output],
        "current_step_id": node_id,
        "current_step_type": "review",
        "review_round": review_round,
        "review_verdict": verdict,
        "review_feedback": feedback,
    }
