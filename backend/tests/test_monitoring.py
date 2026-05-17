"""Tests for monitoring and metrics endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_basic(client: AsyncClient):
    """Basic health check should always return ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "AI-Collab-OS"
    assert data["version"] == "3.0.0"
    assert "env" in data


@pytest.mark.asyncio
async def test_health_detailed(client: AsyncClient):
    """Detailed health check should include DB and Redis status."""
    resp = await client.get("/health/detailed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "uptime" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] in ("healthy", "unhealthy")


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient):
    """Metrics endpoint should return pool and websocket stats."""
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "database_pool" in data
    assert "websocket" in data
    assert "active_rooms" in data["websocket"]
    assert "total_connections" in data["websocket"]
    assert "redis_connected" in data
    assert isinstance(data["redis_connected"], bool)


@pytest.mark.asyncio
async def test_health_no_auth_required(client: AsyncClient):
    """Health endpoints should not require authentication."""
    # No auth header
    resp1 = await client.get("/health")
    assert resp1.status_code == 200

    resp2 = await client.get("/health/detailed")
    assert resp2.status_code == 200

    resp3 = await client.get("/metrics")
    assert resp3.status_code == 200
