"""SQLModel database models.

Importing this package registers all tables on the SQLModel metadata so that
`SQLModel.metadata.create_all` and Alembic autogenerate can see them.
"""

from app.db.models.agent_message import AgentMessage
from app.db.models.api_key import ApiKey
from app.db.models.project import Project
from app.db.models.project_agent import ProjectAgent
from app.db.models.role_template import RoleTemplate
from app.db.models.user import User
from app.db.models.workflow import Workflow, WorkflowStep

__all__ = [
    "AgentMessage",
    "ApiKey",
    "Project",
    "ProjectAgent",
    "RoleTemplate",
    "User",
    "Workflow",
    "WorkflowStep",
]
