import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_e2e_policy_blocks_unauthorized_target(client: AsyncClient):
    """
    E2E VERIFIED — CONTROLLED MOCK TOOL ENVIRONMENT
    Policy gateway blocks unauthorized target.
    """
    # 1. Create assessment with unauthorized target
    res = await client.post("/api/assessments", json={
        "name": "Unauthorized Target",
        "target": "example.com",  # Unauthorized target
        "scope": "Full scan",
        "description": "E2E Policy Test"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assessment_id = data["data"]["id"]

    # 2. Start assessment
    res = await client.post(f"/api/assessments/{assessment_id}/start")
    assert res.status_code == 200

    # 3. Wait for controller execution to complete (poll status)
    max_retries = 10
    status = "CREATED"
    for _ in range(max_retries):
        res = await client.get(f"/api/assessments/{assessment_id}")
        data = res.json()["data"]
        status = data["status"]
        if status in ["COMPLETED", "FAILED", "BLOCKED"]:
            break
        await asyncio.sleep(0.5)

    # 4. Verify final assessment state is BLOCKED
    assert status == "BLOCKED"

    # 5. Verify no evidence was created since it was blocked early
    res = await client.get(f"/api/assessments/{assessment_id}/evidence")
    evidence = res.json()["data"]
    assert len(evidence) == 0

    # 6. Verify Activity Log
    res = await client.get(f"/api/assessments/{assessment_id}/activity")
    activities = res.json()["data"]
    assert len(activities) > 0
    messages = [a["message"] for a in activities]
    assert any("TARGET_NOT_ALLOWED" in m for m in messages)
