"""Tests for agent instance management endpoints."""

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient) -> tuple[str, str, str]:
    """Helper: register user, create project, create role template, return (token, project_id, role_id)."""
    # Register
    resp = await client.post("/api/v1/auth/register", json={
        "username": "agentuser",
        "password": "test123456",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    resp = await client.post("/api/v1/projects", json={
        "name": "Agent测试项目",
    }, headers=headers)
    project_id = resp.json()["id"]

    # Create role template
    resp = await client.post("/api/v1/roles", json={
        "key": "frontend",
        "name": "前端工程师",
        "system_prompt": "你是一个专业的前端工程师，擅长React和TypeScript开发。",
    }, headers=headers)
    role_id = resp.json()["id"]

    return token, project_id, role_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_agent_instance(client: AsyncClient):
    """Should create an agent instance in a project."""
    token, project_id, role_id = await _setup(client)

    resp = await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端1号",
        "provider": "openai",
        "model": "gpt-4o",
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["instance_name"] == "前端1号"
    assert data["instance_index"] == 1
    assert data["status"] == "idle"
    assert data["provider"] == "openai"


@pytest.mark.asyncio
async def test_create_multiple_agents_auto_index(client: AsyncClient):
    """Should auto-increment instance_index for same role."""
    token, project_id, role_id = await _setup(client)
    headers = _auth(token)

    resp1 = await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端1号",
    }, headers=headers)
    assert resp1.json()["instance_index"] == 1

    resp2 = await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端2号",
    }, headers=headers)
    assert resp2.json()["instance_index"] == 2


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Should list all agents in a project."""
    token, project_id, role_id = await _setup(client)
    headers = _auth(token)

    await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端1号",
    }, headers=headers)
    await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端2号",
    }, headers=headers)

    resp = await client.get(f"/api/v1/agents/project/{project_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    """Should update agent configuration."""
    token, project_id, role_id = await _setup(client)
    headers = _auth(token)

    create_resp = await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "前端1号",
    }, headers=headers)
    agent_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/agents/{agent_id}", json={
        "model": "claude-3-5-sonnet",
        "provider": "anthropic",
        "status": "working",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "claude-3-5-sonnet"
    assert data["provider"] == "anthropic"
    assert data["status"] == "working"


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    """Should delete an agent instance."""
    token, project_id, role_id = await _setup(client)
    headers = _auth(token)

    create_resp = await client.post(f"/api/v1/agents/project/{project_id}", json={
        "role_template_id": role_id,
        "instance_name": "待删除Agent",
    }, headers=headers)
    agent_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/agents/{agent_id}", headers=headers)
    assert resp.status_code == 204

    # Verify deleted
    get_resp = await client.get(f"/api/v1/agents/{agent_id}", headers=headers)
    assert get_resp.status_code == 404
