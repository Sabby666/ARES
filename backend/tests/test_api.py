# backend/tests/test_api.py
"""Basic API tests for the ARES prototype."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_dashboard(client: AsyncClient):
    res = await client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    res = await client.get("/api/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) >= 5


@pytest.mark.asyncio
async def test_list_tools(client: AsyncClient):
    res = await client.get("/api/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) >= 5


@pytest.mark.asyncio
async def test_create_and_list_assessment(client: AsyncClient):
    # Create
    res = await client.post("/api/assessments", json={
        "name": "Test Scan",
        "target": "http://localhost:3000",
        "scope": "Full scan",
        "description": "Test assessment",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assessment_id = data["data"]["id"]

    # List
    res = await client.get("/api/assessments")
    assert res.status_code == 200
    data = res.json()
    assert any(a["id"] == assessment_id for a in data["data"])

    # Get detail
    res = await client.get(f"/api/assessments/{assessment_id}")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Test Scan"


@pytest.mark.asyncio
async def test_policy_blocks_external(client: AsyncClient):
    """Assessment with external target should be blocked by policy."""
    res = await client.post("/api/assessments", json={
        "name": "External Scan",
        "target": "http://example.com",
    })
    assert res.status_code == 200
    assessment_id = res.json()["data"]["id"]

    # Start it
    res = await client.post(f"/api/assessments/{assessment_id}/start")
    assert res.status_code == 200

    # Wait a bit for pipeline, then check status
    import asyncio
    await asyncio.sleep(2)

    res = await client.get(f"/api/assessments/{assessment_id}")
    data = res.json()["data"]
    assert data["status"] == "BLOCKED"
