"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown events."""
    # Startup
    setup_logging()

    # Ensure data directory exists for SQLite
    if "sqlite" in settings.database_url:
        from pathlib import Path
        Path("data").mkdir(exist_ok=True)

    await init_db()

    # Connect Redis (cache + pub/sub)
    from app.core.redis import redis_manager
    from app.core.pubsub import redis_pubsub
    await redis_manager.connect()
    await redis_pubsub.start()

    # Seed system role templates
    from app.db.session import async_session_factory
    from app.db.seed import seed_system_roles
    async with async_session_factory() as session:
        await seed_system_roles(session)
        await session.commit()

    yield

    # Shutdown: close Redis pub/sub + connection pool + DB
    await redis_pubsub.stop()
    await redis_manager.disconnect()

    from app.db.session import dispose_engine
    await dispose_engine()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version="3.0.0",
        description="Multi-Agent Collaborative Development Platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    if settings.rate_limit_enabled:
        from app.core.rate_limit import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)

    # Request logging
    from app.core.middleware import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register routers
    _register_routers(app)

    # Global exception handlers
    from app.core.middleware import register_exception_handlers
    register_exception_handlers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Mount all API routers."""
    from app.api.auth import router as auth_router
    from app.api.agents import router as agents_router
    from app.api.roles import router as roles_router
    from app.api.projects import router as projects_router
    from app.api.workflows import router as workflows_router
    from app.api.files import router as files_router
    from app.api.templates import router as templates_router
    from app.api.api_keys import router as api_keys_router
    from app.api.ws import router as ws_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(roles_router, prefix="/api/v1/roles", tags=["roles"])
    app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
    app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["workflows"])
    app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
    app.include_router(templates_router, prefix="/api/v1/templates", tags=["templates"])
    app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["api-keys"])
    app.include_router(ws_router, tags=["websocket"])

    # Monitoring endpoints (no auth required)
    from app.api.monitoring import router as monitoring_router
    app.include_router(monitoring_router, tags=["monitoring"])


app = create_app()
