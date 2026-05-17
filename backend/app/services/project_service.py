"""Project service: CRUD operations for projects."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError, AuthorizationError
from app.db.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Manages project lifecycle."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, data: ProjectCreate) -> Project:
        """Create a new project and initialize workspace."""
        project = Project(
            user_id=user_id,
            name=data.name,
            description=data.description,
            plan=data.plan,
            config=data.config,
        )
        self.session.add(project)
        await self.session.flush()

        # Initialize workspace directory
        workspace = Path(settings.workspace_root) / project.id
        workspace.mkdir(parents=True, exist_ok=True)
        project.workspace_path = str(workspace)
        self.session.add(project)

        return project

    async def list_by_user(self, user_id: str) -> list[Project]:
        """List all projects for a user."""
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, project_id: str, user_id: str) -> Project:
        """Get a project by ID, verifying ownership."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project")
        if project.user_id != user_id:
            raise AuthorizationError(detail="无权访问此项目")
        return project

    async def update(self, project_id: str, user_id: str, data: ProjectUpdate) -> Project:
        """Update project fields."""
        project = await self.get(project_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        # Touch updated_at
        from app.db.models.base import utcnow
        project.updated_at = utcnow()

        self.session.add(project)
        return project

    async def delete(self, project_id: str, user_id: str) -> None:
        """Delete a project (soft: set status=archived)."""
        project = await self.get(project_id, user_id)
        project.status = "archived"
        from app.db.models.base import utcnow
        project.updated_at = utcnow()
        self.session.add(project)
