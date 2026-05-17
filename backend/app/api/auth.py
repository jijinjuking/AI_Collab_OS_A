"""Authentication API routes: register, login, get current user."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserInfo
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/ping")
async def ping():
    """Auth module health check."""
    return {"module": "auth", "status": "ok"}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, session: DBSession):
    """Register a new user and return JWT token."""
    service = AuthService(session)
    user = await service.register(data)
    # Auto-login after registration
    token_resp = await service.login(data.username, data.password)
    return token_resp


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: DBSession):
    """Authenticate user and return JWT token."""
    service = AuthService(session)
    return await service.login(data.username, data.password)


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: CurrentUser):
    """Get current authenticated user info."""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        settings=current_user.settings,
    )
