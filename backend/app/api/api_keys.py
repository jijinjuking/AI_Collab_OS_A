"""API Key management routes."""

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DBSession
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyResponse
from app.services.api_key_service import api_key_service

router = APIRouter()


@router.post("", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(data: ApiKeyCreate, session: DBSession, user: CurrentUser):
    """Create a new API key. The raw key is only shown once."""
    api_key, raw_key = await api_key_service.create(
        session=session,
        user_id=user.id,
        name=data.name,
        scopes=data.scopes,
        expires_at=data.expires_at,
    )
    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(session: DBSession, user: CurrentUser):
    """List all API keys for the current user."""
    keys = await api_key_service.list_by_user(session, user.id)
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            is_active=k.is_active,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post("/{key_id}/revoke")
async def revoke_api_key(key_id: str, session: DBSession, user: CurrentUser):
    """Revoke (deactivate) an API key."""
    success = await api_key_service.revoke(session, key_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {"success": True, "message": "API Key 已撤销"}


@router.delete("/{key_id}")
async def delete_api_key(key_id: str, session: DBSession, user: CurrentUser):
    """Permanently delete an API key."""
    success = await api_key_service.delete(session, key_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {"success": True, "message": "API Key 已删除"}
