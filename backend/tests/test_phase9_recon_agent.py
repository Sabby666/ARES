# backend/tests/test_phase9_recon_agent.py
"""
Phase 9 — ReconAgent Integration Tests

Coverage:
  - SUCCESS path: ReconAgent.scan() → ToolGateway → MockReconAdapter → typed ReconResult
  - BLOCKED path: policy BLOCK → RuntimeError raised, no data fabricated
  - TIMEOUT path: adapter timeout → RuntimeError raised
  - FAILED path: adapter error → RuntimeError raised
  - Determinism: two successive mock calls return identical endpoint sets
  - ReconResult schema: correct types, no extra fields
  - to_controller_dict(): serializes correctly for Controller consumption
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio

from app.agents.recon_agent import ReconAgent
from app.schemas.recon import (
    ReconResult, ReconExecutionMode, ReconEndpoint, ReconTechnology,
)
from app.schemas.tools import ToolResult, ToolExecutionState, ToolRequest
from app.schemas.policy import PolicyDecision, PolicyDecisionResult, ActionCapability
from app.tools.gateway import ToolGateway
from app.tools.adapters.mock import MockReconAdapter


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_allow_decision() -> PolicyDecision:
    return PolicyDecision(
        decision_id=str(uuid.uuid4()),
        action_id=str(uuid.uuid4()),
        decision=PolicyDecisionResult.ALLOW,
        reason="Test authorization",
        reason_code="TEST_ALLOW",
    )


def make_block_decision() -> PolicyDecision:
    return PolicyDecision(
        decision_id=str(uuid.uuid4()),
        action_id=str(uuid.uuid4()),
        decision=PolicyDecisionResult.BLOCK,
        reason="Test block",
        reason_code="TEST_BLOCK",
    )


def make_success_tool_result(target: str = "http://localhost") -> ToolResult:
    """Build the ToolResult that MockReconAdapter would produce."""
    return ToolResult(
        execution_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        capability=ActionCapability.RECON,
        adapter="MockReconAdapter",
        status=ToolExecutionState.SUCCESS,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_ms=1000,
        structured_data={
            "target": target,
            "source": "MockReconAdapter",
            "execution_mode": "SIMULATED",
            "reachable": True,
            "status_code": 200,
            "endpoints_discovered": 2,
            "endpoints": [
                {"path": "/", "method": "GET", "status": 200, "tech": ["HTML5"]},
                {"path": "/login", "method": "POST", "status": 302, "tech": ["Express.js"]},
            ],
            "technologies": [
                {"name": "Node.js", "version": "18.17.0", "category": "Runtime"},
            ],
            "headers": {"Server": "nginx/1.24.0"},
            "open_ports": [80, 443],
            "dns_records": [{"type": "A", "value": "127.0.0.1"}],
            "tls": {"enabled": True, "version": "TLSv1.3"},
            "observations": ["Test observation"],
        },
        metadata={"source": "MockReconAdapter", "execution_mode": "SIMULATED"},
    )


def make_blocked_tool_result() -> ToolResult:
    return ToolResult(
        execution_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        capability=ActionCapability.RECON,
        adapter="Unknown",
        status=ToolExecutionState.BLOCKED,
        error_code="POLICY_NOT_ALLOWED",
        error_message="Tool execution blocked by policy: TEST_BLOCK",
    )


def make_timeout_tool_result() -> ToolResult:
    return ToolResult(
        execution_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        capability=ActionCapability.RECON,
        adapter="MockReconAdapter",
        status=ToolExecutionState.TIMEOUT,
        error_code="TOOL_TIMEOUT",
        error_message="Tool execution timed out after 30 seconds.",
    )


def make_failed_tool_result() -> ToolResult:
    return ToolResult(
        execution_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        capability=ActionCapability.RECON,
        adapter="MockReconAdapter",
        status=ToolExecutionState.FAILED,
        error_code="TOOL_EXECUTION_FAILED",
        error_message="Unexpected failure: connection refused",
    )


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestReconAgentSuccessPath:
    """Tests for the SUCCESS execution path."""

    @pytest.mark.asyncio
    async def test_scan_returns_recon_result_type(self):
        """scan() must return a typed ReconResult, not a raw dict."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_success_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert isinstance(result, ReconResult)

    @pytest.mark.asyncio
    async def test_scan_populates_endpoints(self):
        """Endpoints list must contain typed ReconEndpoint instances."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_success_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert result.endpoints_discovered == 2
        assert len(result.endpoints) == 2
        assert all(isinstance(ep, ReconEndpoint) for ep in result.endpoints)
        assert result.endpoints[0].path == "/"
        assert result.endpoints[1].method == "POST"

    @pytest.mark.asyncio
    async def test_scan_populates_technologies(self):
        """Technologies list must contain typed ReconTechnology instances."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_success_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert len(result.technologies) == 1
        assert isinstance(result.technologies[0], ReconTechnology)
        assert result.technologies[0].name == "Node.js"

    @pytest.mark.asyncio
    async def test_scan_sets_execution_mode_simulated(self):
        """Execution mode must reflect the adapter metadata."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_success_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert result.execution_mode == ReconExecutionMode.SIMULATED

    @pytest.mark.asyncio
    async def test_scan_preserves_tool_execution_reference(self):
        """tool_execution_reference must match the adapter's execution_id."""
        tool_result = make_success_tool_result()
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = tool_result

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert result.tool_execution_reference == tool_result.execution_id

    @pytest.mark.asyncio
    async def test_gateway_called_once_per_scan(self):
        """ToolGateway must be called exactly once per scan invocation."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_success_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        mock_gateway.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_receives_correct_capability(self):
        """ToolGateway must receive a RECON capability in the request."""
        captured_requests = []

        async def capture_execute(request, decision):
            captured_requests.append(request)
            return make_success_tool_result()

        mock_gateway = MagicMock(spec=ToolGateway)
        mock_gateway.execute = capture_execute

        agent = ReconAgent(tool_gateway=mock_gateway)
        await agent.scan(
            target="http://localhost",
            assessment_id="assess-001",
            policy_decision=make_allow_decision(),
        )

        assert len(captured_requests) == 1
        req = captured_requests[0]
        assert isinstance(req, ToolRequest)
        assert req.capability == ActionCapability.RECON
        assert req.target == "http://localhost"
        assert req.assessment_id == "assess-001"


class TestReconAgentFailurePaths:
    """Tests for BLOCKED / TIMEOUT / FAILED states."""

    @pytest.mark.asyncio
    async def test_blocked_decision_raises_runtime_error(self):
        """When ToolGateway returns BLOCKED, ReconAgent must raise RuntimeError."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_blocked_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)

        with pytest.raises(RuntimeError, match="blocked by policy"):
            await agent.scan(
                target="http://localhost",
                assessment_id="assess-001",
                policy_decision=make_allow_decision(),
            )

    @pytest.mark.asyncio
    async def test_timeout_raises_runtime_error(self):
        """When ToolGateway returns TIMEOUT, ReconAgent must raise RuntimeError."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_timeout_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)

        with pytest.raises(RuntimeError, match="timed out"):
            await agent.scan(
                target="http://localhost",
                assessment_id="assess-001",
                policy_decision=make_allow_decision(),
            )

    @pytest.mark.asyncio
    async def test_failed_raises_runtime_error(self):
        """When ToolGateway returns FAILED, ReconAgent must raise RuntimeError."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_failed_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)

        with pytest.raises(RuntimeError, match="tool failed"):
            await agent.scan(
                target="http://localhost",
                assessment_id="assess-001",
                policy_decision=make_allow_decision(),
            )

    @pytest.mark.asyncio
    async def test_no_data_fabricated_on_failure(self):
        """ReconAgent must never return a result when the tool fails."""
        mock_gateway = AsyncMock(spec=ToolGateway)
        mock_gateway.execute.return_value = make_failed_tool_result()

        agent = ReconAgent(tool_gateway=mock_gateway)
        result = None

        try:
            result = await agent.scan(
                target="http://localhost",
                assessment_id="assess-001",
                policy_decision=make_allow_decision(),
            )
        except RuntimeError:
            pass  # expected

        assert result is None, "ReconAgent must not return data on tool failure"


class TestMockReconAdapterDeterminism:
    """Tests for the deterministic MockReconAdapter (no random sampling)."""

    @pytest.mark.asyncio
    async def test_mock_adapter_returns_full_endpoint_set(self):
        """MockReconAdapter must return all 15 fixture endpoints deterministically."""
        adapter = MockReconAdapter()
        req = ToolRequest(
            request_id=str(uuid.uuid4()),
            assessment_id="test",
            target="http://localhost",
            capability=ActionCapability.RECON,
        )
        result = await adapter.execute(req)

        assert result.status == ToolExecutionState.SUCCESS
        sd = result.structured_data
        assert sd["endpoints_discovered"] == 15
        assert len(sd["endpoints"]) == 15

    @pytest.mark.asyncio
    async def test_mock_adapter_is_deterministic(self):
        """Two calls to MockReconAdapter must return identical endpoint sets."""
        adapter = MockReconAdapter()
        req = ToolRequest(
            request_id=str(uuid.uuid4()),
            assessment_id="test",
            target="http://localhost",
            capability=ActionCapability.RECON,
        )

        result1 = await adapter.execute(req)
        result2 = await adapter.execute(req)

        paths1 = {ep["path"] for ep in result1.structured_data["endpoints"]}
        paths2 = {ep["path"] for ep in result2.structured_data["endpoints"]}
        assert paths1 == paths2

    @pytest.mark.asyncio
    async def test_mock_adapter_includes_observations(self):
        """MockReconAdapter must include security observations in structured_data."""
        adapter = MockReconAdapter()
        req = ToolRequest(
            request_id=str(uuid.uuid4()),
            assessment_id="test",
            target="http://localhost",
            capability=ActionCapability.RECON,
        )
        result = await adapter.execute(req)

        observations = result.structured_data.get("observations", [])
        assert len(observations) > 0
        assert any(".env" in obs for obs in observations)

    @pytest.mark.asyncio
    async def test_mock_adapter_includes_execution_mode(self):
        """MockReconAdapter structured_data must include source and execution_mode."""
        adapter = MockReconAdapter()
        req = ToolRequest(
            request_id=str(uuid.uuid4()),
            assessment_id="test",
            target="http://localhost",
            capability=ActionCapability.RECON,
        )
        result = await adapter.execute(req)

        sd = result.structured_data
        assert sd["source"] == "MockReconAdapter"
        assert sd["execution_mode"] == "SIMULATED"


class TestReconResultSchema:
    """Tests for the ReconResult schema and serialization."""

    def test_to_controller_dict_keys(self):
        """to_controller_dict() must include all Controller-expected keys."""
        result = ReconResult(
            target="http://localhost",
            source="MockReconAdapter",
            execution_mode=ReconExecutionMode.SIMULATED,
        )
        d = result.to_controller_dict()

        required_keys = {
            "target", "source", "execution_mode", "reachable",
            "endpoints_discovered", "endpoints", "technologies",
            "headers", "open_ports", "dns_records", "tls", "observations",
        }
        assert required_keys.issubset(set(d.keys()))

    def test_execution_mode_serialized_as_string(self):
        """to_controller_dict() must serialize execution_mode as a plain string."""
        result = ReconResult(
            target="http://localhost",
            source="MockReconAdapter",
            execution_mode=ReconExecutionMode.REAL,
        )
        d = result.to_controller_dict()
        assert d["execution_mode"] == "REAL"
        assert isinstance(d["execution_mode"], str)

    def test_endpoint_list_serialized_as_dicts(self):
        """to_controller_dict() must serialize endpoints as plain dicts."""
        ep = ReconEndpoint(path="/login", method="POST", status=302, tech=["Express.js"])
        result = ReconResult(
            target="http://localhost",
            source="MockReconAdapter",
            execution_mode=ReconExecutionMode.SIMULATED,
            endpoints=[ep],
            endpoints_discovered=1,
        )
        d = result.to_controller_dict()

        assert isinstance(d["endpoints"], list)
        assert isinstance(d["endpoints"][0], dict)
        assert d["endpoints"][0]["path"] == "/login"

    def test_recon_result_defaults_to_reachable(self):
        """Default ReconResult must be reachable=True, endpoints_discovered=0."""
        result = ReconResult(
            target="http://localhost",
            source="MockReconAdapter",
            execution_mode=ReconExecutionMode.SIMULATED,
        )
        assert result.reachable is True
        assert result.endpoints_discovered == 0
        assert result.endpoints == []
        assert result.technologies == []


class TestReconAgentGatewayIntegration:
    """
    Integration tests: ReconAgent + ToolGateway + MockReconAdapter
    (no external network calls).
    """

    @pytest.mark.asyncio
    async def test_full_pipeline_mock_mode(self, monkeypatch):
        """End-to-end: ReconAgent → ToolGateway → MockReconAdapter → ReconResult."""
        from app.core.config import settings
        monkeypatch.setattr(settings, "TOOL_PROVIDER", "mock")

        gateway = ToolGateway()  # real gateway, mock provider mode
        agent = ReconAgent(tool_gateway=gateway)

        allow_decision = PolicyDecision(
            decision_id=str(uuid.uuid4()),
            action_id=str(uuid.uuid4()),
            decision=PolicyDecisionResult.ALLOW,
            reason="Integration test",
            reason_code="TEST_ALLOW",
        )

        result = await agent.scan(
            target="http://localhost",
            assessment_id="integration-001",
            policy_decision=allow_decision,
        )

        assert isinstance(result, ReconResult)
        assert result.execution_mode == ReconExecutionMode.SIMULATED
        assert result.endpoints_discovered == 15
        assert len(result.endpoints) == 15
        assert result.reachable is True
        assert len(result.technologies) == 6
        assert result.tool_execution_reference is not None

    @pytest.mark.asyncio
    async def test_policy_block_prevents_tool_execution(self):
        """ToolGateway must not reach the adapter when policy is BLOCK."""
        gateway = ToolGateway()
        agent = ReconAgent(tool_gateway=gateway)

        block_decision = PolicyDecision(
            decision_id=str(uuid.uuid4()),
            action_id=str(uuid.uuid4()),
            decision=PolicyDecisionResult.BLOCK,
            reason="Unauthorized target",
            reason_code="UNAUTHORIZED_TARGET",
        )

        with pytest.raises(RuntimeError, match="blocked by policy"):
            await agent.scan(
                target="http://unauthorized-target.com",
                assessment_id="integration-002",
                policy_decision=block_decision,
            )
