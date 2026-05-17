"""Role template management routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps import DBSession
from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.role_template import RoleTemplate
from app.db.models.user import User
from app.schemas.agent import RoleTemplateCreate, RoleTemplateOut

router = APIRouter()


@router.get("", response_model=list[RoleTemplateOut])
async def list_roles(
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """List all role templates (system + user's custom)."""
    stmt = select(RoleTemplate).where(
        (RoleTemplate.is_system == True)  # noqa: E712
        | (RoleTemplate.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    templates = result.scalars().all()
    return [_to_out(t) for t in templates]


@router.post("", response_model=RoleTemplateOut, status_code=201)
async def create_role(
    data: RoleTemplateCreate,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Create a custom role template."""
    # Check uniqueness
    stmt = select(RoleTemplate).where(
        RoleTemplate.user_id == current_user.id,
        RoleTemplate.key == data.key,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictError(detail=f"角色 key '{data.key}' 已存在")

    template = RoleTemplate(
        user_id=current_user.id,
        key=data.key,
        name=data.name,
        icon=data.icon,
        system_prompt=data.system_prompt,
        skills=data.skills,
        default_model=data.default_model,
        is_system=False,
    )
    session.add(template)
    await session.flush()
    return _to_out(template)


@router.get("/{role_id}", response_model=RoleTemplateOut)
async def get_role(
    role_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Get a single role template."""
    stmt = select(RoleTemplate).where(RoleTemplate.id == role_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundError("RoleTemplate")
    return _to_out(template)


@router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: str,
    session: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Delete a custom role template (cannot delete system roles)."""
    stmt = select(RoleTemplate).where(RoleTemplate.id == role_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundError("RoleTemplate")
    if template.is_system:
        raise ConflictError(detail="不能删除系统预设角色")
    if template.user_id != current_user.id:
        raise ConflictError(detail="只能删除自己创建的角色")
    await session.delete(template)


def _to_out(t: RoleTemplate) -> RoleTemplateOut:
    return RoleTemplateOut(
        id=t.id,
        key=t.key,
        name=t.name,
        icon=t.icon,
        system_prompt=t.system_prompt,
        skills=t.skills,
        default_model=t.default_model,
        is_system=t.is_system,
        user_id=t.user_id,
    )
