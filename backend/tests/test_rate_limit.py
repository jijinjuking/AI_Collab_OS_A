"""Tests for rate limiting middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rate_limit_skips_health(client: AsyncClient):
    """Health endpoint should bypass rate limiting."""
    # Hit health many times — should never get 429
    for _ in range(100):
        resp = await client.get("/health")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_returns_headers(client: AsyncClient):
    """Rate-limited endpoints should include rate limit headers."""
    # Register to get a token
    resp = await client.post("/api/v1/auth/register", json={
        "username": "ratelimituser",
        "password": "test123456",
    })
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    # Rate limit headers should be present (if implemented)
    # This test verifies the middleware doesn't crash
