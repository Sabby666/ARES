# backend/app/api/routes.py
"""REST and WebSocket API routes for ARES prototype."""

import asyncio
import json
import httpx
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from app.database.engine import get_db, AsyncSessionLocal
from app.models.models import Project, Assessment, Finding, Evidence, ActivityLog, Report
from app.schemas.schemas import (
    APIResponse, AssessmentCreate, AssessmentOut, AssessmentListOut,
    FindingOut, EvidenceOut, ActivityOut, ReportOut,
    DashboardStats, DashboardOut, AgentInfo, ToolInfo,
)
from app.core.config import settings
from app.agents import (
    AresController, PolicyAgent, ReconAgent, AnalyzerAgent, LLMReasoner, ValidationAgent, AgentRegistry
)
from app.tools.tool_adapter import MockToolAdapter

router = APIRouter()
controller = AresController()
tool_adapter = MockToolAdapter()


# ── System Health ─────────────────────────────────────────────────────────

@router.get("/health")
async def api_health():
    """API health status endpoint."""
    return {"status": "healthy"}


# ── Dashboard ─────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Dashboard statistics and recent assessments."""
    total = (await db.execute(select(func.count(Assessment.id)))).scalar() or 0
    running = (await db.execute(
        select(func.count(Assessment.id)).where(Assessment.status.in_(
            ["POLICY_CHECK", "RECON", "ANALYSIS", "LLM_REASONING", "VALIDATION", "EVIDENCE", "REPORTING"]
        ))
    )).scalar() or 0
    completed = (await db.execute(
        select(func.count(Assessment.id)).where(Assessment.status == "COMPLETED")
    )).scalar() or 0

    total_findings = (await db.execute(select(func.count(Finding.id)))).scalar() or 0
    critical = (await db.execute(
        select(func.count(Finding.id)).where(Finding.severity == "Critical")
    )).scalar() or 0
    high = (await db.execute(
        select(func.count(Finding.id)).where(Finding.severity == "High")
    )).scalar() or 0
    medium = (await db.execute(
        select(func.count(Finding.id)).where(Finding.severity == "Medium")
    )).scalar() or 0
    low = (await db.execute(
        select(func.count(Finding.id)).where(Finding.severity == "Low")
    )).scalar() or 0

    # Recent assessments
    result = await db.execute(
        select(Assessment).order_by(desc(Assessment.created_at)).limit(10)
    )
    recent = result.scalars().all()

    recent_out = []
    for a in recent:
        fc = (await db.execute(
            select(func.count(Finding.id)).where(Finding.assessment_id == a.id)
        )).scalar() or 0
        vc = (await db.execute(
            select(func.count(Finding.id)).where((Finding.assessment_id == a.id) & (Finding.status == "VALIDATED"))
        )).scalar() or 0
        cc = (await db.execute(
            select(func.count(Finding.id)).where((Finding.assessment_id == a.id) & (Finding.status == "NEEDS_REVIEW"))
        )).scalar() or 0
        
        mode = "SIMULATED / MOCK" if settings.TOOL_PROVIDER == "mock" else "REAL / HEXSTRIKE"
        summary = f"{vc} Validated, {cc} Candidate"
        
        recent_out.append(AssessmentListOut(
            id=a.id, name=a.name, target=a.target,
            status=a.status, findings_count=fc,
            validation_summary=summary, execution_mode=mode,
            created_at=a.created_at,
        ))

    total_evidence = (await db.execute(select(func.count(Evidence.id)))).scalar() or 0

    stats = DashboardStats(
        total_assessments=total, running=running, completed=completed,
        total_findings=total_findings, critical_findings=critical,
        high_findings=high, medium_findings=medium, low_findings=low,
        total_evidence=total_evidence,
    )
    return APIResponse(data=DashboardOut(stats=stats, recent_assessments=recent_out).model_dump())


# ── Assessments ───────────────────────────────────────────────────────────

@router.get("/assessments", response_model=APIResponse)
async def list_assessments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).order_by(desc(Assessment.created_at)))
    assessments = result.scalars().all()

    out = []
    for a in assessments:
        fc = (await db.execute(
            select(func.count(Finding.id)).where(Finding.assessment_id == a.id)
        )).scalar() or 0
        vc = (await db.execute(
            select(func.count(Finding.id)).where((Finding.assessment_id == a.id) & (Finding.status == "VALIDATED"))
        )).scalar() or 0
        cc = (await db.execute(
            select(func.count(Finding.id)).where((Finding.assessment_id == a.id) & (Finding.status == "NEEDS_REVIEW"))
        )).scalar() or 0
        
        mode = "SIMULATED / MOCK" if settings.TOOL_PROVIDER == "mock" else "REAL / HEXSTRIKE"
        summary = f"{vc} Validated, {cc} Candidate"
        
        out.append(AssessmentListOut(
            id=a.id, name=a.name, target=a.target,
            status=a.status, findings_count=fc,
            validation_summary=summary, execution_mode=mode,
            created_at=a.created_at,
        ))
    return APIResponse(data=[o.model_dump() for o in out])


@router.post("/assessments", response_model=APIResponse)
async def create_assessment(payload: AssessmentCreate, db: AsyncSession = Depends(get_db)):
    # Ensure a default project exists
    result = await db.execute(select(Project).limit(1))
    project = result.scalar_one_or_none()
    if not project:
        project = Project(name="Default Project", description="Auto-created project")
        db.add(project)
        await db.commit()
        await db.refresh(project)

    project_id = payload.project_id or project.id

    assessment = Assessment(
        project_id=project_id,
        name=payload.name,
        target=payload.target,
        scope=payload.scope,
        description=payload.description,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    return APIResponse(data={"id": assessment.id, "status": assessment.status}, message="Assessment created")


@router.get("/assessments/{assessment_id}", response_model=APIResponse)
async def get_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    fc = (await db.execute(
        select(func.count(Finding.id)).where(Finding.assessment_id == assessment_id)
    )).scalar() or 0

    out = AssessmentOut(
        id=assessment.id, project_id=assessment.project_id,
        name=assessment.name, target=assessment.target,
        scope=assessment.scope, description=assessment.description,
        status=assessment.status, started_at=assessment.started_at,
        completed_at=assessment.completed_at, duration_ms=assessment.duration_ms,
        recon_data=assessment.recon_data, analysis_data=assessment.analysis_data,
        reasoning_data=assessment.reasoning_data, findings_count=fc,
        created_at=assessment.created_at,
    )
    return APIResponse(data=out.model_dump())


@router.post("/assessments/{assessment_id}/start", response_model=APIResponse)
async def start_assessment(assessment_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.status not in ("CREATED", "FAILED", "BLOCKED"):
        raise HTTPException(status_code=400, detail=f"Cannot start assessment in '{assessment.status}' state")

    # Reset state
    assessment.status = "CREATED"
    assessment.started_at = None
    assessment.completed_at = None
    assessment.duration_ms = None
    db.add(assessment)
    await db.commit()

    # Run pipeline in background
    async def _run_pipeline():
        async with AsyncSessionLocal() as session:
            await controller.run(session, assessment_id)

    background_tasks.add_task(_run_pipeline)
    return APIResponse(message="Assessment pipeline started")


# ── Findings ──────────────────────────────────────────────────────────────

@router.get("/assessments/{assessment_id}/findings", response_model=APIResponse)
async def get_findings(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Finding)
        .options(joinedload(Finding.evidence))
        .where(Finding.assessment_id == assessment_id)
        .order_by(desc(Finding.created_at))
    )
    findings = result.unique().scalars().all()
    out = [FindingOut.model_validate(f).model_dump() for f in findings]
    return APIResponse(data=out)


@router.get("/findings", response_model=APIResponse)
async def all_findings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Finding)
        .options(joinedload(Finding.evidence))
        .order_by(desc(Finding.created_at))
        .limit(100)
    )
    findings = result.unique().scalars().all()
    out = [FindingOut.model_validate(f).model_dump() for f in findings]
    return APIResponse(data=out)


# ── Evidence ──────────────────────────────────────────────────────────────

@router.get("/assessments/{assessment_id}/evidence", response_model=APIResponse)
async def get_evidence(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Evidence).where(Evidence.assessment_id == assessment_id).order_by(Evidence.timestamp)
    )
    evidence = result.scalars().all()
    out = [EvidenceOut.model_validate(e).model_dump() for e in evidence]
    return APIResponse(data=out)


# ── Activity ──────────────────────────────────────────────────────────────

@router.get("/assessments/{assessment_id}/activity", response_model=APIResponse)
async def get_activity(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.assessment_id == assessment_id).order_by(ActivityLog.timestamp)
    )
    logs = result.scalars().all()
    out = [ActivityOut.model_validate(l).model_dump() for l in logs]
    return APIResponse(data=out)


# ── Reports ───────────────────────────────────────────────────────────────

@router.get("/assessments/{assessment_id}/report", response_model=APIResponse)
async def get_report(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.assessment_id == assessment_id).order_by(desc(Report.generated_at)).limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")
    return APIResponse(data=ReportOut.model_validate(report).model_dump())


@router.get("/assessments/{assessment_id}/report/html")
async def get_report_html(assessment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment or not assessment.report_html:
        raise HTTPException(status_code=404, detail="Report not found")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=assessment.report_html)


# ── Agents ────────────────────────────────────────────────────────────────

@router.get("/agents", response_model=APIResponse)
async def list_agents():
    agents = AgentRegistry.list_agent_info()
    agents.append(AgentInfo(name="Controller", role="Orchestration", description="Orchestrates the multi-agent pipeline and manages state."))
    return APIResponse(data=[a.model_dump() for a in agents])


# ── Tools ─────────────────────────────────────────────────────────────────

@router.get("/tools", response_model=APIResponse)
async def list_tools():
    tools = tool_adapter.list_tools()
    return APIResponse(data=tools)


# ── Global Evidence ───────────────────────────────────────────────────────

@router.get("/evidence", response_model=APIResponse)
async def all_evidence(db: AsyncSession = Depends(get_db)):
    """Return all evidence records across all assessments (newest first, limit 200)."""
    result = await db.execute(
        select(Evidence).order_by(desc(Evidence.timestamp)).limit(200)
    )
    evidence = result.scalars().all()
    out = [EvidenceOut.model_validate(e).model_dump() for e in evidence]
    return APIResponse(data=out)


# ── Settings (safe read-only config) ─────────────────────────────────────

@router.get("/settings", response_model=APIResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Return safe application configuration — no secrets exposed."""
    assessment_count = (await db.execute(select(func.count(Assessment.id)))).scalar() or 0
    finding_count = (await db.execute(select(func.count(Finding.id)))).scalar() or 0
    evidence_count = (await db.execute(select(func.count(Evidence.id)))).scalar() or 0

    # Mask API keys: show only whether configured, never the value
    hexstrike_key_configured = bool(settings.HEXSTRIKE_API_KEY)
    llm_key_configured = bool(settings.LLM_API_KEY)

    # Sanitize base URLs (strip credentials if any embedded in URL)
    hexstrike_url_safe = settings.HEXSTRIKE_BASE_URL.split("@")[-1] if "@" in settings.HEXSTRIKE_BASE_URL else settings.HEXSTRIKE_BASE_URL
    llm_url_safe = settings.LLM_BASE_URL.split("@")[-1] if "@" in settings.LLM_BASE_URL else settings.LLM_BASE_URL

    data = {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "app_env": settings.APP_ENV,
        "tool_provider": settings.TOOL_PROVIDER.upper(),
        "llm_provider": settings.LLM_PROVIDER.upper(),
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": llm_url_safe,
        "llm_api_key_configured": llm_key_configured,
        "hexstrike_base_url": hexstrike_url_safe,
        "hexstrike_api_key_configured": hexstrike_key_configured,
        "allowed_targets": settings.ALLOWED_TARGETS,
        "tool_timeout_seconds": settings.TOOL_TIMEOUT_SECONDS,
        "llm_timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        "database_type": "SQLite (aiosqlite)",
        "database_path": "data/ares.db",
        "total_assessments": assessment_count,
        "total_findings": finding_count,
        "total_evidence": evidence_count,
        "execution_boundary": "LOCAL LABORATORY ONLY",
        "scope_constraint": "Authorized targets: localhost / 127.0.0.1 / demo.local",
    }
    return APIResponse(data=data)


# ── System Health (service status) ───────────────────────────────────────

@router.get("/system/health", response_model=APIResponse)
async def system_health():
    """Check health of backend and external services (HexStrike, OmniRoute)."""

    async def check_hexstrike() -> dict:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(
                    settings.HEXSTRIKE_BASE_URL.replace("/api/v1", "") + "/health",
                    headers={"X-API-Key": settings.HEXSTRIKE_API_KEY} if settings.HEXSTRIKE_API_KEY else {},
                )
                return {"status": "ONLINE", "http_status": r.status_code}
        except httpx.ConnectError:
            return {"status": "OFFLINE", "error": "Connection refused"}
        except httpx.TimeoutException:
            return {"status": "TIMEOUT", "error": "Request timed out"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    async def check_omniroute() -> dict:
        if settings.LLM_PROVIDER != "omniroute":
            return {"status": "DISABLED", "note": f"LLM provider is '{settings.LLM_PROVIDER}'"}
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(
                    settings.LLM_BASE_URL.replace("/v1", "") + "/health",
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"} if settings.LLM_API_KEY else {},
                )
                return {"status": "ONLINE", "http_status": r.status_code}
        except httpx.ConnectError:
            return {"status": "OFFLINE", "error": "Connection refused"}
        except httpx.TimeoutException:
            return {"status": "TIMEOUT", "error": "Request timed out"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    hexstrike_status, omniroute_status = await asyncio.gather(
        check_hexstrike(),
        check_omniroute(),
    )

    return APIResponse(data={
        "backend": {"status": "ONLINE"},
        "hexstrike": hexstrike_status,
        "omniroute": omniroute_status,
        "tool_provider": settings.TOOL_PROVIDER.upper(),
        "llm_provider": settings.LLM_PROVIDER.upper(),
    })


# ── WebSocket ─────────────────────────────────────────────────────────────

@router.websocket("/ws/{assessment_id}")
async def websocket_endpoint(websocket: WebSocket, assessment_id: str):
    await websocket.accept()

    async def send_event(data: dict):
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    controller.register_ws(assessment_id, send_event)

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        controller.unregister_ws(assessment_id, send_event)
