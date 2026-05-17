"""Workflow management routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import get_current_user
from app.api.deps import DBSession
from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.project import Project
from app.db.models.user import User
from app.db.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowListOut,
    WorkflowOut,
    WorkflowStartRequest,
    WorkflowUpdate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("/project/{project_id}", response_model=WorkflowOut, status_code=201)
async def create_workflow(
    project_id: str,
    data: WorkflowCreate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Create a new workflow for a project."""
    await _verify_project(session, project_id, current_user.id)
    service = WorkflowService(session)
    workflow = await service.create(project_id, data)
    return _to_out(workflow)


@router.get("/project/{project_id}", response_model=list[WorkflowListOut])
async def list_workflows(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """List all workflows for a project."""
    await _verify_project(session, project_id, current_user.id)
    service = WorkflowService(session)
    workflows = await service.list_by_project(project_id)
    return [
        WorkflowListOut(
            id=w.id,
            name=w.name,
            type=w.type,
            status=w.status,
            mode=w.mode,
            created_at=w.created_at.isoformat(),
        )
        for w in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Get workflow details."""
    service = WorkflowService(session)
    workflow = await service.get(workflow_id)
    await _verify_project(session, workflow.project_id, current_user.id)
    return _to_out(workflow)


@router.put("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Update workflow (name, dag_config, mode)."""
    service = WorkflowService(session)
    workflow = await service.get(workflow_id)
    await _verify_project(session, workflow.project_id, current_user.id)
    workflow = await service.update(workflow_id, data)
    return _to_out(workflow)


@router.post("/{workflow_id}/start", response_model=WorkflowOut)
async def start_workflow(
    workflow_id: str,
    data: WorkflowStartRequest,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Start a workflow execution."""
    service = WorkflowService(session)
    workflow = await service.get(workflow_id)
    await _verify_project(session, workflow.project_id, current_user.id)
    workflow = await service.start(workflow_id, data.task_description)
    return _to_out(workflow)


@router.post("/{workflow_id}/pause", response_model=WorkflowOut)
async def pause_workflow(
    workflow_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Pause a running workflow."""
    service = WorkflowService(session)
    workflow = await service.get(workflow_id)
    await _verify_project(session, workflow.project_id, current_user.id)
    workflow = await service.pause(workflow_id)
    return _to_out(workflow)


# --- Helpers ---


async def _verify_project(session, project_id: str, user_id: str):
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != user_id:
        raise AuthorizationError(detail="无权访问此项目")


def _to_out(w: Workflow) -> WorkflowOut:
    return WorkflowOut(
        id=w.id,
        project_id=w.project_id,
        name=w.name,
        type=w.type,
        status=w.status,
        dag_config=w.dag_config,
        current_step_id=w.current_step_id,
        mode=w.mode,
        max_review_rounds=w.max_review_rounds,
        started_at=w.started_at.isoformat() if w.started_at else None,
        completed_at=w.completed_at.isoformat() if w.completed_at else None,
        created_at=w.created_at.isoformat(),
        updated_at=w.updated_at.isoformat(),
    )
