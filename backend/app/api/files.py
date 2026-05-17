"""File system routes: sandboxed file operations for project workspaces."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.api.deps import DBSession
from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.project import Project
from app.db.models.user import User
from app.services.file_service import FileService
from sqlalchemy import select

router = APIRouter()


class FileWriteRequest(BaseModel):
    path: str = Field(min_length=1, description="Relative file path")
    content: str = Field(description="File content")


class FileReadResponse(BaseModel):
    path: str
    content: str
    size: int


class FileListResponse(BaseModel):
    path: str
    type: str  # "file" or "dir"
    size: int


class FileTreeResponse(BaseModel):
    tree: str


class MkdirRequest(BaseModel):
    path: str = Field(min_length=1)


async def _get_file_service(
    project_id: str, session: DBSession, current_user: User
) -> FileService:
    """Verify project ownership and return FileService."""
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != current_user.id:
        raise AuthorizationError(detail="无权访问此项目")
    return FileService(project_id)


@router.get("/project/{project_id}/tree", response_model=FileTreeResponse)
async def get_file_tree(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
    max_depth: int = 3,
):
    """Get project workspace file tree."""
    fs = await _get_file_service(project_id, session, current_user)
    return FileTreeResponse(tree=fs.get_tree(max_depth=max_depth))


@router.get("/project/{project_id}/list", response_model=list[FileListResponse])
async def list_files(
    project_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
    path: str = "",
    recursive: bool = False,
):
    """List files in a project workspace directory."""
    fs = await _get_file_service(project_id, session, current_user)
    items = fs.list_files(path, recursive=recursive)
    return [FileListResponse(**item) for item in items]


@router.get("/project/{project_id}/read")
async def read_file(
    project_id: str,
    path: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
) -> FileReadResponse:
    """Read a file from the project workspace."""
    fs = await _get_file_service(project_id, session, current_user)
    content = fs.read_file(path)
    return FileReadResponse(path=path, content=content, size=len(content))


@router.post("/project/{project_id}/write", status_code=201)
async def write_file(
    project_id: str,
    data: FileWriteRequest,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Write a file to the project workspace."""
    fs = await _get_file_service(project_id, session, current_user)
    result = fs.write_file(data.path, data.content)
    return {"success": True, **result}


@router.post("/project/{project_id}/mkdir", status_code=201)
async def mkdir(
    project_id: str,
    data: MkdirRequest,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Create a directory in the project workspace."""
    fs = await _get_file_service(project_id, session, current_user)
    fs.mkdir(data.path)
    return {"success": True, "path": data.path}


@router.delete("/project/{project_id}/delete")
async def delete_file(
    project_id: str,
    path: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Delete a file or directory from the project workspace."""
    fs = await _get_file_service(project_id, session, current_user)
    fs.delete_file(path)
    return {"success": True, "path": path}
