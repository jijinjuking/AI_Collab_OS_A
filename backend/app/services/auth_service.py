"""Authentication service: register, login, token validation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user. Raises ConflictError if username/email taken."""
        # Check username uniqueness
        stmt = select(User).where(User.username == data.username)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError(detail="用户名已存在")

        # Check email uniqueness (if provided)
        if data.email:
            stmt = select(User).where(User.email == data.email)
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ConflictError(detail="邮箱已被注册")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError(detail="用户名或密码错误")

        token = create_access_token(
            subject=user.id,
            extra={"username": user.username, "role": user.role},
        )
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
            role=user.role,
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Fetch user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
