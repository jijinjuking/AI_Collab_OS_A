"""API dependency injection utilities."""

from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_session
from app.services.auth_service import AuthService

# Type alias for DB session dependency
DBSession = Annotated[AsyncSession, Depends(get_session)]

# Auth schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    session: DBSession,
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Security(api_key_header),
) -> User:
    """Unified auth dependency: supports JWT Bearer token OR X-API-Key header.

    Priority: API Key > JWT (if both provided, API Key wins).
    """
    # Try API Key first
    if api_key:
        from app.services.api_key_service import api_key_service
        key_record = await api_key_service.verify(session, api_key)
        if key_record is None:
            raise AuthenticationError(detail="无效或已过期的 API Key")
        service = AuthService(session)
        user = await service.get_user_by_id(key_record.user_id)
        if not user:
            raise AuthenticationError(detail="API Key 关联用户不存在")
        return user

    # Fall back to JWT
    if token:
        payload = decode_access_token(token)
        if not payload:
            raise AuthenticationError(detail="无效的认证令牌")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError(detail="无效的认证令牌")
        service = AuthService(session)
        user = await service.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError(detail="用户不存在")
        return user

    raise AuthenticationError(detail="未提供认证凭据")


# Type alias for authenticated user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
