"""Tests for project CRUD endpoints."""

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    """Helper: register and return token."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "projuser",
        "password": "test123456",
    })
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    """Should create a project."""
    token = await _get_token(client)
    resp = await client.post("/api/v1/projects", json={
        "name": "测试项目",
        "description": "一个测试项目",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "测试项目"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    """Should list user's projects."""
    token = await _get_token(client)
    # Create 2 projects
    await client.post("/api/v1/projects", json={"name": "项目A"}, headers=_auth(token))
    await client.post("/api/v1/projects", json={"name": "项目B"}, headers=_auth(token))

    resp = await client.get("/api/v1/projects", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    """Should get project details."""
    token = await _get_token(client)
    create_resp = await client.post("/api/v1/projects", json={
        "name": "详情项目",
        "plan": "做一个电商系统",
    }, headers=_auth(token))
    project_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{project_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["plan"] == "做一个电商系统"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    """Should update project fields."""
    token = await _get_token(client)
    create_resp = await client.post("/api/v1/projects", json={
        "name": "原始名称",
    }, headers=_auth(token))
    project_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/projects/{project_id}", json={
        "name": "新名称",
        "status": "active",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名称"
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    """Should archive (soft-delete) a project."""
    token = await _get_token(client)
    create_resp = await client.post("/api/v1/projects", json={
        "name": "待删除",
    }, headers=_auth(token))
    project_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{project_id}", headers=_auth(token))
    assert resp.status_code == 204

    # Verify it's archived
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=_auth(token))
    assert get_resp.json()["status"] == "archived"
