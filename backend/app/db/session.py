"""Database session management.

Supports both SQLite (dev) and PostgreSQL (production) with appropriate
connection pool settings.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings


def _build_engine_kwargs() -> dict:
    """Build engine kwargs based on database driver."""
    kwargs: dict = {
        "echo": settings.debug,
        "future": True,
    }

    if "postgresql" in settings.database_url:
        # PostgreSQL production pool settings (from config)
        kwargs.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
        )
    else:
        # SQLite: no pool needed (single-file DB)
        kwargs["connect_args"] = {"check_same_thread": False}

    return kwargs


# Create async engine
engine = create_async_engine(settings.database_url, **_build_engine_kwargs())

# Session factory
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables (dev only).

    In production, use Alembic migrations:
        alembic upgrade head
    """
    if settings.is_prod:
        return  # Production uses Alembic only

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield a database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Gracefully close all connections (call on shutdown)."""
    await engine.dispose()
