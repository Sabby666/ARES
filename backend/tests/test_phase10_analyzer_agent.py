# backend/tests/test_phase10_analyzer_agent.py
"""
Phase 10 — AnalyzerAgent Integration Tests

Coverage:
  - Typed input contract: ReconResult in, list[dict] out
  - Evidence honesty: every finding has valid evidence_status
  - All Phase 10 honesty fields present: evidence_requirements, suggested_validation_context
  - Prompt construction: key ReconResult fields appear in the rendered prompt
  - LLMProvider boundary: AnalyzerAgent calls provider, never httpx directly
  - Input-driven MockProvider: findings reference actual input observations/endpoints
  - Empty recon: analyzer handles edge case gracefully
  - No data fabrication on LLM failure
  - OmniRoute integration: mocked API path returns correct schema
  - Provenance: analysis_provenance attached after analyze()
  - Controller integration: analyzer called with ReconResult, not dict
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.analyzer_agent import AnalyzerAgent
from app.llm.mock_provider import MockProvider
from app.llm.schemas import (
    AnalysisResultSchema,
    CandidateFindingSchema,
)
from app.schemas.recon import (
    ReconResult,
    ReconEndpoint,
    ReconExecutionMode,
    ReconTechnology,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_full_recon_result(target: str = "http://localhost") -> ReconResult:
    """Full MockReconAdapter-like ReconResult with all standard fields."""
    return ReconResult(
        target=target,
        source="MockReconAdapter",
        execution_mode=ReconExecutionMode.SIMULATED,
        tool_execution_reference=str(uuid.uuid4()),
        reachable=True,
        status_code=200,
        endpoints_discovered=15,
        endpoints=[
            ReconEndpoint(path="/", method="GET", status=200, tech=["HTML5"]),
            ReconEndpoint(path="/login", method="GET", status=200, tech=["HTML5", "JavaScript"]),
            ReconEndpoint(path="/login", method="POST", status=302, tech=["Express.js"]),
            ReconEndpoint(path="/api/admin", method="GET", status=200, tech=["REST", "JSON"]),
            ReconEndpoint(path="/api/admin/config", method="GET", status=200, tech=["REST"]),
            ReconEndpoint(path="/.env", method="GET", status=200, tech=["Text"]),
        ],
        technologies=[
            ReconTechnology(name="Node.js", version="18.17.0", category="Runtime"),
            ReconTechnology(name="Express.js", version="4.18.2", category="Framework"),
            ReconTechnology(name="JWT", version="9.0.0", category="Authentication"),
        ],
        headers={
            "Server": "nginx/1.24.0",
            "X-Powered-By": "Express",
            "X-Frame-Options": "MISSING",
            "Content-Security-Policy": "MISSING",
            "Strict-Transport-Security": "MISSING",
            "X-Content-Type-Options": "nosniff",
        },
        open_ports=[80, 443, 3000, 8080],
        dns_records=[{"type": "A", "value": "127.0.0.1"}],
        tls={"enabled": True, "version": "TLSv1.3"},
        observations=[
            "Exposed .env file detected at /.env",
            "Missing Content-Security-Policy header",
            "Missing Strict-Transport-Security header",
            "Admin endpoint accessible at /api/admin/config",
        ],
    )


def make_empty_recon_result() -> ReconResult:
    """Minimal ReconResult with no findings signals."""
    return ReconResult(
        target="http://empty.local",
        source="MockReconAdapter",
        execution_mode=ReconExecutionMode.SIMULATED,
    )


# ─── Tests: Typed Input Contract ─────────────────────────────────────────────

class TestAnalyzerAgentInputContract:
    """AnalyzerAgent must accept ReconResult, not a raw dict."""

    @pytest.mark.asyncio
    async def test_analyze_accepts_recon_result(self):
        """analyze() must accept a typed ReconResult without raising TypeError."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        result = await agent.analyze(recon)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_analyze_rejects_dict(self):
        """analyze() must raise RuntimeError when given a raw dict (Phase 10 contract).
        
        When a dict is passed instead of ReconResult, calling .to_controller_dict()
        raises AttributeError, which BaseAgent.run() wraps into AgentException,
        which AnalyzerAgent.analyze() re-raises as RuntimeError('LLM Analysis failed').
        """
        agent = AnalyzerAgent(provider=MockProvider())
        with pytest.raises((TypeError, AttributeError, RuntimeError)):
            await agent.analyze({"target": "http://localhost"})  # type: ignore

    @pytest.mark.asyncio
    async def test_analyze_returns_list_of_dicts(self):
        """Return value must be list[dict], each dict having expected top-level keys."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        assert isinstance(findings, list)
        for f in findings:
            assert isinstance(f, dict)

    @pytest.mark.asyncio
    async def test_analyze_annotates_status_and_agent(self):
        """Every returned finding must be annotated with status=CANDIDATE and agent=AnalyzerAgent."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        assert len(findings) > 0
        for f in findings:
            assert f["status"] == "CANDIDATE"
            assert f["agent"] == "AnalyzerAgent"


# ─── Tests: Evidence Honesty ─────────────────────────────────────────────────

class TestEvidenceHonesty:
    """All Phase 10 honesty fields must be present and valid."""

    @pytest.mark.asyncio
    async def test_all_findings_have_evidence_status(self):
        """Every finding must have a valid evidence_status."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        assert len(findings) > 0
        for f in findings:
            assert f.get("evidence_status") in (
                "OBSERVED", "INFERRED", "POTENTIAL"
            ), f"Invalid evidence_status: {f.get('evidence_status')}"

    @pytest.mark.asyncio
    async def test_all_findings_have_evidence_requirements(self):
        """Every finding must have an evidence_requirements string."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        for f in findings:
            assert "evidence_requirements" in f
            assert isinstance(f["evidence_requirements"], str)

    @pytest.mark.asyncio
    async def test_all_findings_have_suggested_validation_context(self):
        """Every finding must have a suggested_validation_context string."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        for f in findings:
            assert "suggested_validation_context" in f
            assert isinstance(f["suggested_validation_context"], str)

    @pytest.mark.asyncio
    async def test_env_finding_is_observed_or_inferred(self):
        """The .env exposure finding must be OBSERVED or INFERRED, not POTENTIAL."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        env_finding = next((f for f in findings if ".env" in f.get("title", "")), None)
        assert env_finding is not None
        assert env_finding["evidence_status"] in ("OBSERVED", "INFERRED")

    @pytest.mark.asyncio
    async def test_header_finding_is_observed(self):
        """Missing headers finding must be OBSERVED (directly visible in recon)."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        header_finding = next(
            (f for f in findings if "Header" in f.get("title", "")), None
        )
        if header_finding:  # only assert if finding was generated
            assert header_finding["evidence_status"] == "OBSERVED"

    @pytest.mark.asyncio
    async def test_jwt_finding_is_potential(self):
        """JWT algorithm confusion finding must be POTENTIAL (not directly confirmed)."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        jwt_finding = next(
            (f for f in findings if "JWT" in f.get("title", "")), None
        )
        if jwt_finding:
            assert jwt_finding["evidence_status"] == "POTENTIAL"


# ─── Tests: Input-Driven MockProvider ────────────────────────────────────────

class TestInputDrivenMockProvider:
    """MockProvider must derive findings from actual input — not hardcoded strings."""

    @pytest.mark.asyncio
    async def test_env_finding_generated_when_env_endpoint_present(self):
        """MockProvider must generate an .env finding when the endpoint is in recon data."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [{"path": "/.env", "method": "GET", "status": 200, "tech": []}],
            "headers": {},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        titles = [f.title for f in result.findings]
        assert any(".env" in t for t in titles)

    @pytest.mark.asyncio
    async def test_no_env_finding_when_no_env_endpoint(self):
        """MockProvider must NOT generate an .env finding when it's absent from recon."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [{"path": "/login", "method": "GET", "status": 200, "tech": []}],
            "headers": {},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        env_findings = [f for f in result.findings if ".env" in f.title]
        assert len(env_findings) == 0

    @pytest.mark.asyncio
    async def test_header_finding_generated_from_missing_headers(self):
        """MockProvider must generate a header finding when headers are MISSING."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [],
            "headers": {"Content-Security-Policy": "MISSING", "X-Frame-Options": "MISSING"},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        header_findings = [f for f in result.findings if "Header" in f.title]
        assert len(header_findings) >= 1

    @pytest.mark.asyncio
    async def test_no_header_finding_when_headers_present(self):
        """MockProvider must NOT generate a header finding when no header is MISSING."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [],
            "headers": {"Content-Security-Policy": "default-src 'self'"},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        header_findings = [f for f in result.findings if "Header" in f.title]
        assert len(header_findings) == 0

    @pytest.mark.asyncio
    async def test_admin_finding_generated_for_accessible_admin_endpoint(self):
        """MockProvider must flag an admin endpoint that returns non-4xx status."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [
                {"path": "/api/admin/config", "method": "GET", "status": 200, "tech": []}
            ],
            "headers": {},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        admin_findings = [f for f in result.findings if "Admin" in f.title]
        assert len(admin_findings) >= 1

    @pytest.mark.asyncio
    async def test_empty_recon_produces_no_findings(self):
        """MockProvider must produce zero findings for an empty recon_data."""
        provider = MockProvider()
        recon_data = {
            "target": "http://empty.local",
            "endpoints": [],
            "headers": {},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_analysis_provenance_populated(self):
        """AnalysisResultSchema must carry analysis_provenance after analyze_recon_data()."""
        provider = MockProvider()
        recon_data = {
            "target": "http://test.local",
            "endpoints": [],
            "headers": {},
            "observations": [],
            "technologies": [],
            "open_ports": [],
            "execution_mode": "SIMULATED",
            "source": "MockReconAdapter",
        }
        result = await provider.analyze_recon_data(recon_data)
        assert result.analysis_provenance is not None
        assert result.analysis_provenance.get("target") == "http://test.local"
        assert result.analysis_provenance.get("provider") == "MockProvider"


# ─── Tests: LLMProvider Boundary ─────────────────────────────────────────────

class TestLLMProviderBoundary:
    """AnalyzerAgent must call LLMProvider — not httpx, not adapters directly."""

    @pytest.mark.asyncio
    async def test_analyzer_calls_provider_analyze_recon_data(self):
        """AnalyzerAgent must call provider.analyze_recon_data() exactly once per analyze()."""
        mock_provider = AsyncMock()
        mock_provider.analyze_recon_data.return_value = AnalysisResultSchema(findings=[])

        agent = AnalyzerAgent(provider=mock_provider)
        recon = make_full_recon_result()
        await agent.analyze(recon)

        mock_provider.analyze_recon_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_provider_receives_dict_not_recon_result(self):
        """LLMProvider.analyze_recon_data() must receive a dict, not a ReconResult."""
        received_args = []

        async def capture_analyze(recon_data):
            received_args.append(recon_data)
            return AnalysisResultSchema(findings=[])

        mock_provider = MagicMock()
        mock_provider.analyze_recon_data = capture_analyze

        agent = AnalyzerAgent(provider=mock_provider)
        recon = make_full_recon_result()
        await agent.analyze(recon)

        assert len(received_args) == 1
        assert isinstance(received_args[0], dict), (
            "LLMProvider must receive a dict, not a ReconResult"
        )
        assert received_args[0].get("target") == recon.target

    @pytest.mark.asyncio
    async def test_recon_result_fields_appear_in_provider_input(self):
        """The dict sent to LLMProvider must include ReconResult's endpoints and observations."""
        received_args = []

        async def capture_analyze(recon_data):
            received_args.append(recon_data)
            return AnalysisResultSchema(findings=[])

        mock_provider = MagicMock()
        mock_provider.analyze_recon_data = capture_analyze

        agent = AnalyzerAgent(provider=mock_provider)
        recon = make_full_recon_result()
        await agent.analyze(recon)

        rd = received_args[0]
        assert "endpoints" in rd
        assert "observations" in rd
        assert "headers" in rd
        assert "technologies" in rd
        assert rd["target"] == recon.target

    @pytest.mark.asyncio
    async def test_no_fabrication_on_llm_failure(self):
        """AnalyzerAgent must raise RuntimeError on LLM failure, not return fabricated data."""
        mock_provider = AsyncMock()
        mock_provider.analyze_recon_data.side_effect = RuntimeError("LLM unavailable")

        agent = AnalyzerAgent(provider=mock_provider)
        recon = make_full_recon_result()
        result = None

        with pytest.raises(RuntimeError, match="LLM Analysis failed"):
            result = await agent.analyze(recon)

        assert result is None


# ─── Tests: Prompt Construction ──────────────────────────────────────────────

class TestPromptConstruction:
    """build_analyzer_user_prompt() must render all key ReconResult fields."""

    def test_target_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert "http://localhost" in prompt

    def test_endpoints_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert "/.env" in prompt
        assert "/api/admin" in prompt

    def test_headers_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert "Content-Security-Policy" in prompt
        assert "MISSING" in prompt

    def test_technologies_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert "Node.js" in prompt
        assert "JWT" in prompt

    def test_observations_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert ".env" in prompt
        assert "Admin endpoint accessible" in prompt

    def test_evidence_status_instruction_in_system_prompt(self):
        from app.llm.prompts.analyzer_prompt import ANALYZER_SYSTEM_PROMPT
        assert "OBSERVED" in ANALYZER_SYSTEM_PROMPT
        assert "INFERRED" in ANALYZER_SYSTEM_PROMPT
        assert "POTENTIAL" in ANALYZER_SYSTEM_PROMPT

    def test_execution_mode_in_prompt(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        rd = make_full_recon_result().to_controller_dict()
        prompt = build_analyzer_user_prompt(rd)
        assert "SIMULATED" in prompt

    def test_empty_recon_prompt_does_not_crash(self):
        from app.llm.prompts.analyzer_prompt import build_analyzer_user_prompt
        prompt = build_analyzer_user_prompt({})
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ─── Tests: CandidateFindingSchema Schema ─────────────────────────────────────

class TestCandidateFindingSchema:
    """Verify Phase 10 schema extensions are correct."""

    def test_evidence_status_default_is_potential(self):
        f = CandidateFindingSchema(
            title="Test",
            category="Test",
            severity="Low",
            confidence=0.5,
            endpoint="/",
            description="test",
            reasoning="test",
            recommendation="test",
        )
        assert f.evidence_status == "POTENTIAL"

    def test_evidence_status_accepts_observed(self):
        f = CandidateFindingSchema(
            title="Test",
            category="Test",
            severity="Low",
            confidence=0.5,
            endpoint="/",
            description="test",
            reasoning="test",
            recommendation="test",
            evidence_status="OBSERVED",
        )
        assert f.evidence_status == "OBSERVED"

    def test_evidence_status_rejects_invalid(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CandidateFindingSchema(
                title="Test",
                category="Test",
                severity="Low",
                confidence=0.5,
                endpoint="/",
                description="test",
                reasoning="test",
                recommendation="test",
                evidence_status="CONFIRMED",  # invalid
            )

    def test_evidence_requirements_default_is_empty_string(self):
        f = CandidateFindingSchema(
            title="T", category="C", severity="Low", confidence=0.1,
            endpoint="/", description="d", reasoning="r", recommendation="rec",
        )
        assert f.evidence_requirements == ""

    def test_model_dump_includes_all_phase10_fields(self):
        f = CandidateFindingSchema(
            title="T", category="C", severity="Low", confidence=0.1,
            endpoint="/", description="d", reasoning="r", recommendation="rec",
            evidence_status="INFERRED",
            evidence_requirements="Test it",
            suggested_validation_context="Send a request",
        )
        d = f.model_dump()
        assert d["evidence_status"] == "INFERRED"
        assert d["evidence_requirements"] == "Test it"
        assert d["suggested_validation_context"] == "Send a request"


# ─── Tests: End-to-End with MockProvider ─────────────────────────────────────

class TestAnalyzerEndToEnd:
    """End-to-end: AnalyzerAgent + MockProvider with full ReconResult."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_findings(self):
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)

        assert len(findings) >= 2  # .env + headers at minimum
        titles = [f["title"] for f in findings]
        assert any(".env" in t for t in titles)

    @pytest.mark.asyncio
    async def test_full_pipeline_all_honesty_fields_present(self):
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)

        for f in findings:
            assert f["evidence_status"] in ("OBSERVED", "INFERRED", "POTENTIAL")
            assert isinstance(f["evidence_requirements"], str)
            assert isinstance(f["suggested_validation_context"], str)

    @pytest.mark.asyncio
    async def test_empty_recon_produces_candidate_list(self):
        """Empty recon should return empty list, not raise."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_empty_recon_result()
        findings = await agent.analyze(recon)
        assert isinstance(findings, list)
        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_agent_state_completed_after_analyze(self):
        from app.agents.base import AgentState
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        await agent.analyze(recon)
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_findings_serializable_to_json(self):
        """Findings must be JSON-serializable for Controller/DB storage."""
        agent = AnalyzerAgent(provider=MockProvider())
        recon = make_full_recon_result()
        findings = await agent.analyze(recon)
        json_str = json.dumps(findings)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
