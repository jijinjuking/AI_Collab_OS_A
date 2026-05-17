"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Should register a new user and return token."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "test123456",
        "email": "test@example.com",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["username"] == "testuser"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Should reject duplicate username."""
    payload = {"username": "dupuser", "password": "test123456"}
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Should login with correct credentials."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "password": "mypassword",
    })
    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "mypassword",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["username"] == "loginuser"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Should reject wrong password."""
    await client.post("/api/v1/auth/register", json={
        "username": "wrongpw",
        "password": "correct123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "wrongpw",
        "password": "incorrect",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Should return user info with valid token."""
    # Register and get token
    reg_resp = await client.post("/api/v1/auth/register", json={
        "username": "meuser",
        "password": "test123456",
    })
    token = reg_resp.json()["access_token"]

    # Get /me
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "meuser"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Should reject unauthenticated request."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
