import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import select, func
from app.database.engine import AsyncSessionLocal
from app.models.models import Project, Assessment, Finding, Evidence, ActivityLog, Report
from app.agents.controller import AresController
from app.schemas.tools import ToolResult, ToolExecutionState
from app.core.config import settings


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def test_project(db_session):
    result = await db_session.execute(select(Project).limit(1))
    project = result.scalar_one_or_none()
    if not project:
        project = Project(name="Controller Test Project", description="Testing AresController")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_controller_happy_path_progression_and_persistence(monkeypatch, db_session, test_project):
    # Force mock providers
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    
    # We want a small bounded test loop, mock MAX_VAPT_ACTIONS
    monkeypatch.setattr(settings, "MAX_VAPT_ACTIONS", 2)
    
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="Happy Path Controller Test",
        target="demo.local",
        scope="Full scan",
        description="Testing complete pipeline progression"
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    # Execute controller pipeline
    await controller.run(db_session, assessment.id)

    # Reload assessment from DB
    res = await db_session.execute(select(Assessment).where(Assessment.id == assessment.id))
    updated = res.scalar_one_or_none()

    assert updated is not None
    assert updated.status == "COMPLETED"
    assert updated.started_at is not None
    assert updated.completed_at is not None
    assert updated.duration_ms is not None and updated.duration_ms >= 0
    assert updated.recon_data is not None
    assert updated.reasoning_data is not None
    assert updated.report_json is not None

    # Verify Activity Logs
    log_res = await db_session.execute(
        select(ActivityLog).where(ActivityLog.assessment_id == assessment.id).order_by(ActivityLog.timestamp)
    )
    logs = log_res.scalars().all()
    assert len(logs) > 0
    log_messages = [l.message for l in logs]
    assert any("Dispatching initial reconnaissance" in m for m in log_messages)
    assert any("Complete!" in m for m in log_messages)


@pytest.mark.asyncio
async def test_controller_policy_block(monkeypatch, db_session, test_project):
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="Policy Block Test",
        target="unauthorized-domain.com",
        scope="Full scan",
        description="Testing policy rejection"
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    await controller.run(db_session, assessment.id)

    res = await db_session.execute(select(Assessment).where(Assessment.id == assessment.id))
    updated = res.scalar_one_or_none()

    assert updated.status == "BLOCKED"
    assert updated.completed_at is not None
    assert updated.recon_data is None

    log_res = await db_session.execute(
        select(ActivityLog).where(ActivityLog.assessment_id == assessment.id)
    )
    logs = log_res.scalars().all()
    assert any("BLOCKED" in l.message for l in logs)


@pytest.mark.asyncio
async def test_controller_recon_stage_failure(monkeypatch, db_session, test_project):
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="Recon Failure Test",
        target="127.0.0.1",
        scope="Full scan",
        description="Testing recon tool failure handling"
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    with patch.object(controller.recon, "scan", side_effect=RuntimeError("Simulated Recon Failure")):
        await controller.run(db_session, assessment.id)

    res = await db_session.execute(select(Assessment).where(Assessment.id == assessment.id))
    updated = res.scalar_one_or_none()

    assert updated.status == "FAILED"
    assert updated.completed_at is not None

    log_res = await db_session.execute(
        select(ActivityLog).where(ActivityLog.assessment_id == assessment.id)
    )
    logs = log_res.scalars().all()
    assert any("Recon failed: Simulated Recon Failure" in l.message for l in logs)


@pytest.mark.asyncio
async def test_controller_stage_exception(monkeypatch, db_session, test_project):
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="Stage Exception Test",
        target="127.0.0.1",
        scope="Full scan",
        description="Testing unhandled exception in stage"
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    # Mock analyzer to raise exception
    with patch.object(controller.analyzer, "analyze", side_effect=RuntimeError("Analyzer crashed")):
        await controller.run(db_session, assessment.id)

    res = await db_session.execute(select(Assessment).where(Assessment.id == assessment.id))
    updated = res.scalar_one_or_none()

    assert updated.status == "FAILED"
    assert updated.completed_at is not None

    log_res = await db_session.execute(
        select(ActivityLog).where(ActivityLog.assessment_id == assessment.id)
    )
    logs = log_res.scalars().all()
    assert any("Analyzer crashed" in l.message for l in logs)


@pytest.mark.asyncio
async def test_controller_websocket_callback_broadcasting(monkeypatch, db_session, test_project):
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "MAX_VAPT_ACTIONS", 1)
    
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="WS Broadcast Test",
        target="demo.local",
        scope="Full scan",
        description="Testing WebSocket event broadcasting"
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    events_received = []

    async def ws_callback(data):
        events_received.append(data)

    controller.register_ws(assessment.id, ws_callback)
    await controller.run(db_session, assessment.id)
    controller.unregister_ws(assessment.id, ws_callback)

    assert len(events_received) > 0
    status_events = [e for e in events_received if e.get("event") == "status"]
    activity_events = [e for e in events_received if e.get("event") == "activity"]

    assert len(status_events) > 0
    assert len(activity_events) > 0
    assert status_events[-1].get("status") == "COMPLETED"


@pytest.mark.asyncio
async def test_controller_nonexistent_assessment(db_session):
    controller = AresController()
    await controller.run(db_session, "invalid-uuid-12345")


@pytest.mark.asyncio
async def test_controller_duplicate_run_prevention(db_session, test_project):
    controller = AresController()
    assessment = Assessment(
        project_id=test_project.id,
        name="Duplicate Run Test",
        target="demo.local",
        status="COMPLETED",
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    await controller.run(db_session, assessment.id)
    res = await db_session.execute(select(Assessment).where(Assessment.id == assessment.id))
    assert res.scalar_one_or_none().status == "COMPLETED"
