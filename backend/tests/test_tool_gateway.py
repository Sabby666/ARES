import pytest
import uuid
import asyncio
from app.tools.gateway import ToolGateway
from app.schemas.tools import ToolRequest, ToolExecutionState
from app.schemas.policy import PolicyDecision, PolicyDecisionResult, ActionCapability


@pytest.fixture
def gateway():
    return ToolGateway()


def create_decision(allow=True) -> PolicyDecision:
    if allow:
        return PolicyDecision(decision=PolicyDecisionResult.ALLOW, reason_code="ALLOWED", reason="Test")
    return PolicyDecision(decision=PolicyDecisionResult.BLOCK, reason_code="BLOCKED", reason="Test")


def create_request(capability=ActionCapability.RECON) -> ToolRequest:
    return ToolRequest(
        request_id=str(uuid.uuid4()),
        assessment_id="test",
        target="demo.local",
        capability=capability,
    )


@pytest.mark.asyncio
async def test_blocked_policy(gateway):
    decision = create_decision(allow=False)
    request = create_request()
    result = await gateway.execute(request, decision)
    assert result.status == ToolExecutionState.BLOCKED
    assert result.error_code == "POLICY_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_unknown_capability(gateway):
    decision = create_decision(allow=True)
    request = create_request(capability="UNKNOWN_CAP")
    result = await gateway.execute(request, decision)
    assert result.status == ToolExecutionState.FAILED
    assert result.error_code == "TOOL_NOT_REGISTERED"


@pytest.mark.asyncio
async def test_successful_execution(gateway):
    decision = create_decision(allow=True)
    request = create_request(capability=ActionCapability.RECON)
    result = await gateway.execute(request, decision)
    assert result.status == ToolExecutionState.SUCCESS
    assert result.adapter == "MockReconAdapter"
    assert "endpoints_discovered" in result.structured_data


@pytest.mark.asyncio
async def test_timeout_execution(gateway, monkeypatch):
    # Monkeypatch settings to have a very low timeout
    import app.core.config
    monkeypatch.setattr(app.core.config.settings, "TOOL_TIMEOUT_SECONDS", 0.01)
    
    decision = create_decision(allow=True)
    request = create_request(capability=ActionCapability.RECON)
    
    result = await gateway.execute(request, decision)
    assert result.status == ToolExecutionState.TIMEOUT
    assert result.error_code == "TOOL_TIMEOUT"
