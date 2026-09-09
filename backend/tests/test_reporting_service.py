import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.models import Assessment, Finding, Evidence, ActivityLog, Report, Project
from app.database.engine import AsyncSessionLocal
from app.services.reporting_service import ReportingService
from app.core.config import settings

@pytest.mark.asyncio
async def test_reporting_service_generation():
    async with AsyncSessionLocal() as db_session:
        # Setup test data
        project = Project(name="Test Project", description="Test Description")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        assessment = Assessment(
            project_id=project.id,
            name="Test Assessment",
            target="http://demo.local",
            status="REPORTING",
            started_at=datetime.now(timezone.utc),
            duration_ms=1000
        )
        db_session.add(assessment)
        await db_session.commit()
        await db_session.refresh(assessment)
    
        # 1 Proven Finding
        f1 = Finding(
            assessment_id=assessment.id,
            title="XSS",
            category="Injection",
            severity="High",
            confidence=0.9,
            endpoint="/search",
            description="XSS found",
            reasoning="Because of script tag",
            recommendation="Escape output",
            status="PROVEN",
            agent="AnalyzerAgent"
        )
        db_session.add(f1)
        
        # 1 Candidate Finding
        f2 = Finding(
            assessment_id=assessment.id,
            title="CSRF",
            category="Auth",
            severity="Medium",
            confidence=0.5,
            endpoint="/login",
            description="No CSRF token",
            reasoning="Missing token",
            recommendation="Add token",
            status="CANDIDATE",
            agent="AnalyzerAgent"
        )
        db_session.add(f2)
        await db_session.commit()
        await db_session.refresh(f1)
        
        # Evidence for f1
        ev = Evidence(
            assessment_id=assessment.id,
            finding_id=f1.id,
            agent="ToolGateway",
            action="scan",
            evidence_type="TOOL_OUTPUT",
            content="<script>alert(1)</script>",
            source="MockScanner",
            source_type="MOCK",
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(ev)
        
        # Activity
        act = ActivityLog(
            assessment_id=assessment.id,
            agent="Controller",
            message="Started assessment",
            log_type="info",
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(act)
        await db_session.commit()
        
        # Temporarily set tool provider
        orig_provider = settings.TOOL_PROVIDER
        settings.TOOL_PROVIDER = "mock"
        
        html = await ReportingService.generate_report(db_session, assessment.id)
        
        settings.TOOL_PROVIDER = orig_provider
        
        # Assertions
        assert "ARES Penetration Testing Report" in html
        assert "Test Assessment" in html
        assert "http://demo.local" in html
        assert "SIMULATED / MOCK" in html
        assert "1 PROVEN" in html or "1</b> were PROVEN" in html or "<strong>1</strong> were PROVEN" in html
        
        # Findings presence
        assert "XSS" in html
        assert "CSRF" in html
        
        # Escaping
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
        assert "<script>alert(1)</script>" not in html
        
        # Badges
        assert "SIMULATED EVIDENCE" in html
        
        # Report persistence
        result = await db_session.execute(select(Report).where(Report.assessment_id == assessment.id))
        report = result.scalar_one_or_none()
        assert report is not None
        assert report.findings_count == 1
        assert assessment.report_html == html
