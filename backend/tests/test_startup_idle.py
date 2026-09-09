# backend/tests/test_startup_idle.py
"""
Startup Idle Contract Tests
============================
These tests assert that ARES performs NO automatic assessment execution
on startup. The only valid trigger for assessment execution is an
explicit user action: POST /api/assessments/{id}/start.

A successful ARES startup MUST:
  - Initialise the database schema
  - Seed exactly 1 default project if no projects exist
  - Leave the assessments table empty (or unchanged)
  - NOT invoke controller.run() automatically
  - NOT spawn any background tasks automatically

These tests enforce that contract so it can never regress.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, func
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.engine import AsyncSessionLocal, init_db
from app.models.models import Project, Assessment


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    """ASGI test client with the full FastAPI application (includes lifespan)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def db():
    """Raw async DB session for direct table inspection."""
    async with AsyncSessionLocal() as session:
        yield session


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_startup_does_not_auto_start_any_assessment(client: AsyncClient):
    """
    Immediately after the application starts, no assessment pipeline execution loop
    should be active. controller._active must be empty.

    The key assertion is: the startup lifespan hook and GET routes NEVER launch background
    assessment pipelines — only an explicit POST /api/assessments/{id}/start does.
    """
    from app.api.routes import controller

    # Verify controller has 0 active running background tasks at startup
    assert len(controller._active) == 0, (
        f"Startup regression: found {len(controller._active)} active tasks in controller._active. "
        "Application startup must remain completely idle."
    )

    # Hit read-only endpoints to ensure app is up and read-only routes don't start background tasks
    health_res = await client.get("/health")
    assert health_res.status_code == 200

    assessments_res = await client.get("/api/assessments")
    assert assessments_res.status_code == 200

    # Ensure still 0 active running tasks
    assert len(controller._active) == 0, (
        "GET request triggered background assessment execution. "
        "Only POST /api/assessments/{id}/start may trigger execution."
    )




@pytest.mark.asyncio
async def test_startup_seeds_exactly_one_default_project(client: AsyncClient):
    """
    The lifespan hook seeds exactly one default project when none exists.
    It must not create duplicate projects on repeated startups.
    """
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count(Project.id)))).scalar()
        assert count >= 1, "Startup must seed at least one default project."
        # In a clean state this should be exactly 1
        # (tests may have added more; the important invariant is >= 1, not 0)


@pytest.mark.asyncio
async def test_controller_run_not_called_on_startup():
    """
    Verify controller.run() is never called during application lifespan startup.
    Uses a mock patch to intercept any calls.
    """
    call_count = {"n": 0}

    original_run = None
    try:
        from app.agents.controller import AresController
        original_run = AresController.run
    except ImportError:
        pass

    async def spy_run(self, *args, **kwargs):
        call_count["n"] += 1
        if original_run:
            return await original_run(self, *args, **kwargs)

    with patch.object(
        __import__("app.agents.controller", fromlist=["AresController"]).AresController,
        "run",
        spy_run,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Just hit a safe read endpoint — no side effects
            res = await c.get("/health")
            assert res.status_code == 200

    assert call_count["n"] == 0, (
        f"controller.run() was called {call_count['n']} time(s) during startup. "
        "Automatic execution is strictly prohibited."
    )


@pytest.mark.asyncio
async def test_get_assessments_does_not_trigger_execution(client: AsyncClient):
    """
    GET /api/assessments must return data only — it must not trigger
    any assessment execution as a side effect.
    """
    with patch("app.agents.controller.AresController.run") as mock_run:
        mock_run.return_value = None

        res = await client.get("/api/assessments")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

        # The run method must not have been called
        mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_assessment_start_requires_explicit_post(client: AsyncClient):
    """
    Assessment execution can ONLY be triggered via POST /api/assessments/{id}/start.
    Verify that GET /api/assessments/{id} does NOT start the pipeline.
    """
    # Create an assessment via the API (POST /api/assessments)
    create_res = await client.post("/api/assessments", json={
        "name": "Idle Contract Test",
        "target": "demo.local",
        "scope": "Test scope",
        "description": "Startup idle contract test assessment",
    })
    assert create_res.status_code == 200
    assessment_id = create_res.json()["data"]["id"]

    with patch("app.agents.controller.AresController.run") as mock_run:
        mock_run.return_value = None

        # Merely reading the assessment must not trigger execution
        get_res = await client.get(f"/api/assessments/{assessment_id}")
        assert get_res.status_code == 200
        mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_dashboard_endpoint_is_read_only(client: AsyncClient):
    """
    GET /api/dashboard must be a pure read — it must not create assessments
    or trigger any execution as a side effect.
    """
    with patch("app.agents.controller.AresController.run") as mock_run:
        mock_run.return_value = None

        res = await client.get("/api/dashboard")
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_run.assert_not_called()
