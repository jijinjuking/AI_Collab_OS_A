"""Tests for API Key management endpoints."""

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    """Helper: register and return token."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "apikeyuser",
        "password": "test123456",
    })
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient):
    """Should create an API key and return raw key once."""
    token = await _get_token(client)
    resp = await client.post("/api/v1/api-keys", json={
        "name": "测试Key",
        "scopes": "read,write",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "测试Key"
    assert data["scopes"] == "read,write"
    assert data["is_active"] is True
    assert "raw_key" in data
    assert len(data["raw_key"]) > 20
    assert data["key_prefix"] == data["raw_key"][:8]


@pytest.mark.asyncio
async def test_create_api_key_with_expiry(client: AsyncClient):
    """Should create an API key with expiration date."""
    token = await _get_token(client)
    resp = await client.post("/api/v1/api-keys", json={
        "name": "过期Key",
        "scopes": "read",
        "expires_at": "2099-12-31T23:59:59",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["expires_at"] is not None


@pytest.mark.asyncio
async def test_create_api_key_validation(client: AsyncClient):
    """Should reject empty name."""
    token = await _get_token(client)
    resp = await client.post("/api/v1/api-keys", json={
        "name": "",
        "scopes": "read",
    }, headers=_auth(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient):
    """Should list all user's API keys without raw_key."""
    token = await _get_token(client)
    headers = _auth(token)

    # Create 2 keys
    await client.post("/api/v1/api-keys", json={"name": "Key1"}, headers=headers)
    await client.post("/api/v1/api-keys", json={"name": "Key2"}, headers=headers)

    resp = await client.get("/api/v1/api-keys", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # raw_key should NOT be in list response
    for key in data:
        assert "raw_key" not in key
        assert "key_prefix" in key


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient):
    """Should revoke (deactivate) an API key."""
    token = await _get_token(client)
    headers = _auth(token)

    create_resp = await client.post("/api/v1/api-keys", json={
        "name": "待撤销Key",
    }, headers=headers)
    key_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/api-keys/{key_id}/revoke", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify it's inactive in list
    list_resp = await client.get("/api/v1/api-keys", headers=headers)
    keys = list_resp.json()
    revoked = next(k for k in keys if k["id"] == key_id)
    assert revoked["is_active"] is False


@pytest.mark.asyncio
async def test_revoke_nonexistent_key(client: AsyncClient):
    """Should return 404 for non-existent key."""
    token = await _get_token(client)
    resp = await client.post(
        "/api/v1/api-keys/nonexistent-id/revoke",
        headers=_auth(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_api_key(client: AsyncClient):
    """Should permanently delete an API key."""
    token = await _get_token(client)
    headers = _auth(token)

    create_resp = await client.post("/api/v1/api-keys", json={
        "name": "待删除Key",
    }, headers=headers)
    key_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/api-keys/{key_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify it's gone from list
    list_resp = await client.get("/api/v1/api-keys", headers=headers)
    ids = [k["id"] for k in list_resp.json()]
    assert key_id not in ids


@pytest.mark.asyncio
async def test_delete_nonexistent_key(client: AsyncClient):
    """Should return 404 for non-existent key."""
    token = await _get_token(client)
    resp = await client.delete(
        "/api/v1/api-keys/nonexistent-id",
        headers=_auth(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_key_isolation(client: AsyncClient):
    """User A should not see User B's keys."""
    # Register user A
    resp_a = await client.post("/api/v1/auth/register", json={
        "username": "keyuser_a",
        "password": "test123456",
    })
    token_a = resp_a.json()["access_token"]

    # Register user B
    resp_b = await client.post("/api/v1/auth/register", json={
        "username": "keyuser_b",
        "password": "test123456",
    })
    token_b = resp_b.json()["access_token"]

    # User A creates a key
    await client.post("/api/v1/api-keys", json={
        "name": "A的Key",
    }, headers=_auth(token_a))

    # User B should see empty list
    list_resp = await client.get("/api/v1/api-keys", headers=_auth(token_b))
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_api_key_requires_auth(client: AsyncClient):
    """Should reject unauthenticated requests."""
    resp = await client.get("/api/v1/api-keys")
    assert resp.status_code == 401
