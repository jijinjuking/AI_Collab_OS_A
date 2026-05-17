"""API Key management service."""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey
from app.db.models.base import utcnow


def _generate_key() -> str:
    """Generate a random API key with 'ak_' prefix."""
    return f"ak_{secrets.token_urlsafe(32)}"


def _hash_key(raw_key: str) -> str:
    """SHA-256 hash of the raw key for storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


class ApiKeyService:
    """CRUD operations for API keys."""

    async def create(
        self,
        session: AsyncSession,
        user_id: str,
        name: str,
        scopes: str = "read,write",
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """Create a new API key. Returns (model, raw_key).

        The raw key is only available at creation time.
        """
        raw_key = _generate_key()
        key_hash = _hash_key(raw_key)
        key_prefix = raw_key[:11]  # "ak_" + first 8 chars

        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes,
            expires_at=expires_at,
        )
        session.add(api_key)
        await session.flush()
        return api_key, raw_key

    async def list_by_user(self, session: AsyncSession, user_id: str) -> list[ApiKey]:
        """List all API keys for a user (without exposing hashes)."""
        stmt = (
            select(ApiKey)
            .where(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def verify(self, session: AsyncSession, raw_key: str) -> ApiKey | None:
        """Verify a raw API key. Returns the ApiKey if valid, None otherwise."""
        key_hash = _hash_key(raw_key)
        stmt = select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,  # noqa: E712
        )
        result = await session.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        # Update last_used_at
        api_key.last_used_at = utcnow()
        return api_key

    async def revoke(self, session: AsyncSession, key_id: str, user_id: str) -> bool:
        """Revoke (deactivate) an API key. Returns True if found and revoked."""
        stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        result = await session.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return False

        api_key.is_active = False
        return True

    async def delete(self, session: AsyncSession, key_id: str, user_id: str) -> bool:
        """Permanently delete an API key."""
        stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        result = await session.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return False

        await session.delete(api_key)
        return True


# Singleton
api_key_service = ApiKeyService()
