"""Tests for workflow management endpoints."""

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient) -> tuple[str, str]:
    """Helper: register user, create project, return (token, project_id)."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "wfuser",
        "password": "test123456",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/projects", json={
        "name": "工作流测试项目",
    }, headers=headers)
    project_id = resp.json()["id"]

    return token, project_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


SAMPLE_DAG = {
    "nodes": [
        {"id": "discuss", "type": "discuss"},
        {"id": "assign", "type": "assign"},
        {"id": "execute", "type": "execute"},
        {"id": "review", "type": "review"},
    ],
    "edges": [
        {"source": "discuss", "target": "assign"},
        {"source": "assign", "target": "execute"},
        {"source": "execute", "target": "review"},
    ],
}


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient):
    """Should create a workflow for a project."""
    token, project_id = await _setup(client)
    resp = await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "name": "全栈开发流程",
        "type": "full",
        "dag_config": SAMPLE_DAG,
        "mode": "manual",
        "max_review_rounds": 3,
    }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "全栈开发流程"
    assert data["type"] == "full"
    assert data["status"] == "draft"
    assert data["mode"] == "manual"
    assert data["max_review_rounds"] == 3
    assert data["dag_config"] == SAMPLE_DAG


@pytest.mark.asyncio
async def test_create_workflow_invalid_type(client: AsyncClient):
    """Should reject invalid workflow type."""
    token, project_id = await _setup(client)
    resp = await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "type": "invalid_type",
        "dag_config": SAMPLE_DAG,
    }, headers=_auth(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_workflow_auto_mode(client: AsyncClient):
    """Should create workflow with auto mode."""
    token, project_id = await _setup(client)
    resp = await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "type": "backend",
        "dag_config": SAMPLE_DAG,
        "mode": "auto",
    }, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["mode"] == "auto"


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient):
    """Should list all workflows for a project."""
    token, project_id = await _setup(client)
    headers = _auth(token)

    # Create 2 workflows
    await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "type": "full",
        "dag_config": SAMPLE_DAG,
    }, headers=headers)
    await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "type": "frontend",
        "dag_config": SAMPLE_DAG,
    }, headers=headers)

    resp = await client.get(f"/api/v1/workflows/project/{project_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient):
    """Should get workflow details by ID."""
    token, project_id = await _setup(client)
    headers = _auth(token)

    create_resp = await client.post(f"/api/v1/workflows/project/{project_id}", json={
        "name": "详情测试",
        "type": "custom",
        "dag_config": SAMPLE_DAG,
        "max_review_rounds": 5,
    }, headers=headers)
    workflow_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/workflows/{workflow_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "详情测试"
    assert data["max_review_rounds"] == 5
    assert data["dag_config"]["nodes"] == SAMPLE_DAG["nodes"]


@pytest.mark.asyncio
async def test_workflow_project_isolation(client: AsyncClient):
    """User should not access another user's project workflows."""
    # User A
    resp_a = await client.post("/api/v1/auth/register", json={
        "username": "wf_user_a",
        "password": "test123456",
    })
    token_a = resp_a.json()["access_token"]

    proj_resp = await client.post("/api/v1/projects", json={
        "name": "A的项目",
    }, headers=_auth(token_a))
    project_id_a = proj_resp.json()["id"]

    await client.post(f"/api/v1/workflows/project/{project_id_a}", json={
        "type": "full",
        "dag_config": SAMPLE_DAG,
    }, headers=_auth(token_a))

    # User B
    resp_b = await client.post("/api/v1/auth/register", json={
        "username": "wf_user_b",
        "password": "test123456",
    })
    token_b = resp_b.json()["access_token"]

    # User B tries to access User A's project workflows
    resp = await client.get(
        f"/api/v1/workflows/project/{project_id_a}",
        headers=_auth(token_b),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_workflow_requires_auth(client: AsyncClient):
    """Should reject unauthenticated requests."""
    resp = await client.get("/api/v1/workflows/project/some-id")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_workflow_nonexistent_project(client: AsyncClient):
    """Should return 404 for non-existent project."""
    token, _ = await _setup(client)
    resp = await client.post("/api/v1/workflows/project/nonexistent-id", json={
        "type": "full",
        "dag_config": SAMPLE_DAG,
    }, headers=_auth(token))
    assert resp.status_code == 404
