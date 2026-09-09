import pytest
import asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.agents.controller import AresController


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_e2e_assessment_happy_path(monkeypatch, client: AsyncClient):
    """
    E2E VERIFIED — CONTROLLED MOCK TOOL ENVIRONMENT
    Happy path pipeline execution.
    """
    # Force mock providers in settings so any newly-created adapters use mock
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "MAX_VAPT_ACTIONS", 2)

    # The module-level `controller` in routes.py was created at import time with
    # live providers (hexstrike + omniroute). Replace it with a fresh instance
    # that reads the monkeypatched settings.
    fresh_controller = AresController()
    with patch("app.api.routes.controller", fresh_controller):
        # 1. Create assessment
        res = await client.post("/api/assessments", json={
            "name": "E2E Happy Path",
            "target": "demo.local",  # Authorized target
            "scope": "Full scan",
            "description": "E2E Test"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assessment_id = data["data"]["id"]

        # 3. Verify initial state
        res = await client.get(f"/api/assessments/{assessment_id}")
        assert res.json()["data"]["status"] == "CREATED"

        # 4. Start assessment
        res = await client.post(f"/api/assessments/{assessment_id}/start")
        assert res.status_code == 200

        # 5. Wait for controller execution to complete (poll status)
        max_retries = 60
        status = "CREATED"
        for _ in range(max_retries):
            res = await client.get(f"/api/assessments/{assessment_id}")
            data = res.json()["data"]
            status = data["status"]
            if status in ["COMPLETED", "FAILED", "BLOCKED"]:
                break
            await asyncio.sleep(0.5)

        # 17. Verify final assessment state
        assert status == "COMPLETED", f"Assessment did not complete successfully. Ended in state {status}."

        # 13. Verify evidence creation
        res = await client.get(f"/api/assessments/{assessment_id}/evidence")
        evidence = res.json()["data"]
        assert len(evidence) > 0, "No evidence generated."

        # 14. Verify finding creation
        res = await client.get(f"/api/assessments/{assessment_id}/findings")
        findings = res.json()["data"]
        assert len(findings) > 0, "No findings generated."

        # 15. Verify validation state
        # Ensure at least one finding has a valid status
        assert any(f["status"] in ["PROVEN", "NOT_PROVEN", "CANDIDATE", "HYPOTHESIS", "VALIDATING"] for f in findings)

        # 16. Verify report generation
        res = await client.get(f"/api/assessments/{assessment_id}/report")
        assert res.status_code == 200
        report = res.json()["data"]
        assert report["content"] is not None
        assert len(report["content"]) > 0

        # Verify Activity Log
        res = await client.get(f"/api/assessments/{assessment_id}/activity")
        activities = res.json()["data"]
        assert len(activities) > 0
        # Check that we transitioned through stages
        messages = [a["message"] for a in activities]
        assert any("Dispatching initial reconnaissance" in m for m in messages)
        assert any("Complete!" in m for m in messages)

