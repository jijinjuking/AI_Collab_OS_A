"""Project management routes."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.deps import DBSession
from app.db.models.user import User
from app.schemas.project import ProjectCreate, ProjectListOut, ProjectOut, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    data: ProjectCreate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    service = ProjectService(session)
    project = await service.create(current_user.id, data)
    return _to_out(project)


@router.get("", response_model=list[ProjectListOut])
async def list_projects(
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """List all projects for the current user."""
    service = ProjectService(session)
    projects = await service.list_by_user(current_user.id)
    return [
        ProjectListOut(
            id=p.id,
            name=p.name,
            status=p.status,
            description=p.description,
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Get project details."""
    service = ProjectService(session)
    project = await service.get(project_id, current_user.id)
    return _to_out(project)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Update a project."""
    service = ProjectService(session)
    project = await service.update(project_id, current_user.id, data)
    return _to_out(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Archive (soft-delete) a project."""
    service = ProjectService(session)
    await service.delete(project_id, current_user.id)


def _to_out(p) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        description=p.description,
        plan=p.plan,
        status=p.status,
        config=p.config,
        workspace_path=p.workspace_path,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )
