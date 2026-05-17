"""Agent chat and instance management routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps import DBSession
from app.core.exceptions import NotFoundError, AuthorizationError
from app.core.sse import sse_response
from app.db.models.project import Project
from app.db.models.project_agent import ProjectAgent
from app.db.models.user import User
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentInstanceCreate,
    AgentInstanceOut,
    AgentInstanceUpdate,
)
from app.services.agent_service import AgentService

router = APIRouter()


# --- Instance Management ---


@router.get("/project/{project_id}", response_model=list[AgentInstanceOut])
async def list_agents(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """List all agent instances in a project."""
    await _verify_project_access(session, project_id, current_user.id)
    stmt = (
        select(ProjectAgent)
        .where(ProjectAgent.project_id == project_id)
        .order_by(ProjectAgent.created_at)
    )
    result = await session.execute(stmt)
    agents = result.scalars().all()
    return [_to_out(a) for a in agents]


@router.post("/project/{project_id}", response_model=AgentInstanceOut, status_code=201)
async def create_agent(
    project_id: str,
    data: AgentInstanceCreate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Create a new agent instance in a project."""
    await _verify_project_access(session, project_id, current_user.id)

    # Calculate next instance_index for this role in this project
    stmt = select(func.coalesce(func.max(ProjectAgent.instance_index), 0)).where(
        ProjectAgent.project_id == project_id,
        ProjectAgent.role_template_id == data.role_template_id,
    )
    result = await session.execute(stmt)
    next_index = result.scalar_one() + 1

    agent = ProjectAgent(
        project_id=project_id,
        role_template_id=data.role_template_id,
        instance_name=data.instance_name,
        instance_index=next_index,
        provider=data.provider,
        base_url=data.base_url,
        model=data.model,
        system_prompt_override=data.system_prompt_override,
        config=data.config,
    )
    session.add(agent)
    await session.flush()
    return _to_out(agent)


@router.get("/{agent_id}", response_model=AgentInstanceOut)
async def get_agent(
    agent_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Get a single agent instance."""
    agent = await _get_agent_with_access(session, agent_id, current_user.id)
    return _to_out(agent)


@router.patch("/{agent_id}", response_model=AgentInstanceOut)
async def update_agent(
    agent_id: str,
    data: AgentInstanceUpdate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Update an agent instance configuration."""
    agent = await _get_agent_with_access(session, agent_id, current_user.id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    from app.db.models.base import utcnow
    agent.updated_at = utcnow()
    session.add(agent)
    await session.flush()
    return _to_out(agent)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Delete an agent instance."""
    agent = await _get_agent_with_access(session, agent_id, current_user.id)
    await session.delete(agent)


# --- Chat ---


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: str,
    request: AgentChatRequest,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Send a message to an agent (streaming or non-streaming)."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)

    if request.stream:
        generator = service.chat_stream(agent, request)
        return sse_response(generator)

    response = await service.chat(agent, request)
    return AgentChatResponse(
        content=response.content,
        model_used=response.model,
        token_count=response.total_tokens,
        message_id="",
    )


# --- Helpers ---


async def _verify_project_access(
    session: AsyncSession, project_id: str, user_id: str
) -> Project:
    """Verify user owns the project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != user_id:
        raise AuthorizationError(detail="无权访问此项目")
    return project


async def _get_agent_with_access(
    session: AsyncSession, agent_id: str, user_id: str
) -> ProjectAgent:
    """Get agent and verify user has access via project ownership."""
    stmt = select(ProjectAgent).where(ProjectAgent.id == agent_id)
    result = await session.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent")
    await _verify_project_access(session, agent.project_id, user_id)
    return agent


def _to_out(a: ProjectAgent) -> AgentInstanceOut:
    return AgentInstanceOut(
        id=a.id,
        project_id=a.project_id,
        role_template_id=a.role_template_id,
        instance_name=a.instance_name,
        instance_index=a.instance_index,
        status=a.status,
        provider=a.provider,
        base_url=a.base_url,
        model=a.model,
        system_prompt_override=a.system_prompt_override,
        config=a.config,
        token_used=a.token_used,
        created_at=a.created_at.isoformat(),
        updated_at=a.updated_at.isoformat(),
    )
