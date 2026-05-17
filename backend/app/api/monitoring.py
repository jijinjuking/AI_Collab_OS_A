"""Monitoring and health check endpoints."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter
from loguru import logger

from app.config import settings
from app.core.redis import redis_manager

router = APIRouter()

# Track app start time for uptime calculation
_start_time = time.time()


@router.get("/health")
async def health_check():
    """Basic health check — always fast, used by load balancers."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": "3.0.0",
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check — includes DB, Redis, uptime.

    Use for monitoring dashboards, not for LB probes (may be slow).
    """
    checks = {}

    # Database check
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    checks["redis"] = await redis_manager.health_check()

    # System info
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    overall_status = "healthy" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "app": settings.app_name,
        "env": settings.app_env,
        "version": "3.0.0",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/metrics")
async def metrics():
    """Basic application metrics for monitoring.

    Returns connection pool stats, WebSocket room counts, etc.
    """
    from app.core.websocket import ws_manager
    from app.db.session import engine

    pool_status = {}
    if hasattr(engine.pool, "status"):
        pool_status = {
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
        }

    ws_rooms = ws_manager.get_all_rooms()

    return {
        "database_pool": pool_status,
        "websocket": {
            "active_rooms": len(ws_rooms),
            "total_connections": sum(ws_rooms.values()),
            "rooms": ws_rooms,
        },
        "redis_connected": redis_manager.is_connected,
    }
