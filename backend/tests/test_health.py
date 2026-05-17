"""Smoke tests for application startup."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """App should respond to health check."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "AI-Collab-OS"


@pytest.mark.asyncio
async def test_auth_ping(client: AsyncClient):
    """Auth module should respond to ping."""
    resp = await client.get("/api/v1/auth/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "auth"
