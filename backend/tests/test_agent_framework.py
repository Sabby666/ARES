# backend/tests/test_agent_framework.py
"""Focused test suite for the ARES Agent Framework (Phase 8)."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.agents.base import BaseAgent, AgentState, AgentResult, AgentException
from app.agents.policy_agent import PolicyAgent
from app.agents.recon_agent import ReconAgent
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.llm_reasoner import LLMReasoner
from app.agents.validation_agent import ValidationAgent
from app.agents.registry import AgentRegistry
from app.schemas.policy import PolicyAction, ActionCapability, PolicyDecisionResult


class DummyCustomAgent(BaseAgent):
    NAME = "DummyAgent"
    ROLE = "Test Role"
    DESCRIPTION = "Test Description"

    async def execute_task(self, should_fail: bool = False) -> str:
        res = await self.run("execute_task", self._task, should_fail)
        return res.payload

    async def _task(self, should_fail: bool):
        if should_fail:
            raise ValueError("Deliberate test failure")
        return "task_success"


@pytest.mark.asyncio
async def test_base_agent_initialization():
    agent = BaseAgent(name="CustomAgent", role="CustomRole", description="CustomDesc")
    assert agent.name == "CustomAgent"
    assert agent.role == "CustomRole"
    assert agent.description == "CustomDesc"
    assert agent.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_agent_lifecycle_and_successful_execution():
    agent = DummyCustomAgent()
    assert agent.state == AgentState.IDLE

    res_val = await agent.execute_task(should_fail=False)
    assert res_val == "task_success"
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_agent_failure_behavior():
    agent = DummyCustomAgent()
    assert agent.state == AgentState.IDLE

    with pytest.raises(AgentException) as exc_info:
        await agent.execute_task(should_fail=True)

    assert agent.state == AgentState.FAILED
    assert exc_info.value.agent_name == "DummyAgent"
    assert exc_info.value.operation == "execute_task"
    assert "Deliberate test failure" in exc_info.value.message


@pytest.mark.asyncio
async def test_agent_result_structure():
    agent = DummyCustomAgent()

    async def dummy_op():
        await asyncio.sleep(0.01)
        return {"data": 123}

    res = await agent.run("dummy_op", dummy_op)

    assert isinstance(res, AgentResult)
    assert res.agent_name == "DummyAgent"
    assert res.role == "Test Role"
    assert res.status == AgentState.COMPLETED
    assert res.payload == {"data": 123}
    assert res.execution_time_ms > 0
    assert res.error is None


@pytest.mark.asyncio
async def test_policy_agent_contract_and_boundary():
    agent = PolicyAgent()
    assert agent.name == "PolicyAgent"
    assert agent.role == "Policy & Governance"

    # Evaluate authorized action
    action = PolicyAction(
        action_id="act-1",
        assessment_id="asst-1",
        target="demo.local",
        action_type="scan",
        capability=ActionCapability.RECON,
        requested_by="TestRunner"
    )
    
    class DummyAssessment:
        target = "demo.local"
        status = "CREATED"

    decision = await agent.evaluate_action(action, DummyAssessment())
    assert decision.decision == PolicyDecisionResult.ALLOW
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_recon_agent_mock_contract(monkeypatch):
    """Phase 9: ReconAgent.scan() requires assessment_id + policy_decision."""
    import uuid as _uuid
    from app.core.config import settings
    from app.schemas.policy import PolicyDecision, PolicyDecisionResult
    from app.schemas.recon import ReconResult, ReconExecutionMode

    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")

    allow_decision = PolicyDecision(
        decision_id=str(_uuid.uuid4()),
        action_id=str(_uuid.uuid4()),
        decision=PolicyDecisionResult.ALLOW,
        reason="Framework test authorization",
        reason_code="TEST_ALLOW",
    )

    agent = ReconAgent()
    assert agent.name == "ReconAgent"
    assert agent.role == "Reconnaissance"

    recon_result = await agent.scan(
        target="demo.local",
        assessment_id="framework-test-001",
        policy_decision=allow_decision,
    )
    assert isinstance(recon_result, ReconResult)
    assert recon_result.target == "demo.local"
    assert recon_result.endpoints_discovered > 0
    assert len(recon_result.endpoints) > 0
    assert len(recon_result.technologies) > 0
    assert recon_result.execution_mode == ReconExecutionMode.SIMULATED
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_analyzer_agent_contract():
    """Phase 10: AnalyzerAgent.analyze() accepts typed ReconResult."""
    import uuid as _uuid
    from app.llm.mock_provider import MockProvider
    from app.schemas.recon import ReconResult, ReconExecutionMode, ReconEndpoint, ReconTechnology

    agent = AnalyzerAgent()
    agent.provider = MockProvider()
    assert agent.name == "AnalyzerAgent"
    assert agent.role == "Vulnerability Analysis"

    sample_recon = ReconResult(
        target="demo.local",
        source="MockReconAdapter",
        execution_mode=ReconExecutionMode.SIMULATED,
        tool_execution_reference=str(_uuid.uuid4()),
        endpoints_discovered=1,
        endpoints=[ReconEndpoint(path="/.env", method="GET", status=200, tech=["Text"])],
        technologies=[ReconTechnology(name="Node.js", version="18.17.0", category="Runtime")],
        observations=["Exposed .env file detected at /.env"],
        headers={"Server": "nginx/1.24.0", "Content-Security-Policy": "MISSING"},
    )

    findings = await agent.analyze(sample_recon)
    assert isinstance(findings, list)
    assert len(findings) > 0
    # All findings must carry evidence_status (Phase 10)
    for f in findings:
        assert f.get("evidence_status") in ("OBSERVED", "INFERRED", "POTENTIAL")
        assert f.get("status") == "CANDIDATE"
        assert f.get("agent") == "AnalyzerAgent"
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_llm_reasoner_contract():
    from app.llm.mock_provider import MockProvider
    agent = LLMReasoner()
    agent.provider = MockProvider()
    assert agent.name == "LLMReasoner"
    assert agent.role == "LLM Reasoning & Prioritization"

    sample_findings = [{
        "title": "Exposed .env",
        "category": "Information Disclosure",
        "severity": "Critical",
        "confidence": 0.95,
        "endpoint": "/.env"
    }]
    sample_recon = {"target": "demo.local"}

    reasoning_res = await agent.reason(sample_findings, sample_recon)
    assert "prioritized_findings" in reasoning_res
    assert "risk_score" in reasoning_res
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_validation_agent_contract(monkeypatch):
    import uuid as _uuid
    from app.core.config import settings
    from app.schemas.policy import PolicyDecision, PolicyDecisionResult
    
    monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")
    
    agent = ValidationAgent()
    assert agent.name == "ValidationAgent"
    assert agent.role == "Finding Validation"

    sample_findings = [{
        "title": "Exposed .env",
        "confidence": 0.9,
    }]
    
    mock_decision = PolicyDecision(
        decision_id=str(_uuid.uuid4()),
        action_id=str(_uuid.uuid4()),
        decision=PolicyDecisionResult.ALLOW,
        reason="test",
        reason_code="TEST",
    )

    validated = await agent.validate(
        target="demo.local", 
        assessment_id="test", 
        policy_decision=mock_decision, 
        findings=sample_findings
    )
    assert len(validated) == 1
    assert validated[0]["status"] == "VALIDATED"
    assert agent.state == AgentState.COMPLETED


def test_agent_registry():
    registered_names = [a.name for a in AgentRegistry.list_agent_info()]
    assert "PolicyAgent" in registered_names
    assert "ReconAgent" in registered_names
    assert "AnalyzerAgent" in registered_names
    assert "LLMReasoner" in registered_names
    assert "ValidationAgent" in registered_names

    recon_inst = AgentRegistry.create_agent("ReconAgent")
    assert isinstance(recon_inst, ReconAgent)
