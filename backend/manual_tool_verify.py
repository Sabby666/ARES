import asyncio
import uuid
from app.tools.gateway import ToolGateway
from app.schemas.tools import ToolRequest, ToolExecutionState
from app.schemas.policy import PolicyDecision, PolicyDecisionResult, ActionCapability


async def run_manual_verification():
    gateway = ToolGateway()
    assessment_id = str(uuid.uuid4())
    target = "http://demo.local"

    print("========================================")
    print("MANUAL TOOL VERIFICATION RESULTS")
    print("========================================")

    # TEST A - Allowed mock capability
    req_a = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability=ActionCapability.RECON)
    dec_a = PolicyDecision(decision=PolicyDecisionResult.ALLOW, reason_code="ALLOWED", reason="Test")
    res_a = await gateway.execute(req_a, dec_a)
    print(f"TEST A (Allowed mock capability) -> {res_a.status.value} (Adapter: {res_a.adapter})")

    # TEST B - Blocked policy
    req_b = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability=ActionCapability.RECON)
    dec_b = PolicyDecision(decision=PolicyDecisionResult.BLOCK, reason_code="BLOCKED_BY_POLICY", reason="Test")
    res_b = await gateway.execute(req_b, dec_b)
    print(f"TEST B (Blocked policy) -> {res_b.status.value} (Error: {res_b.error_code})")

    # TEST C - Unknown capability
    req_c = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability="ARBITRARY_EXECUTION")
    res_c = await gateway.execute(req_c, dec_a)
    print(f"TEST C (Unknown capability) -> {res_c.status.value} (Error: {res_c.error_code})")

    # TEST D - Adapter timeout
    import app.core.config
    original_timeout = app.core.config.settings.TOOL_TIMEOUT_SECONDS
    app.core.config.settings.TOOL_TIMEOUT_SECONDS = 0.01
    
    req_d = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability=ActionCapability.RECON)
    res_d = await gateway.execute(req_d, dec_a)
    print(f"TEST D (Adapter timeout) -> {res_d.status.value} (Error: {res_d.error_code})")
    
    app.core.config.settings.TOOL_TIMEOUT_SECONDS = original_timeout

    # TEST E - Adapter failure
    # We simulate adapter failure by passing a mock adapter that raises an exception
    class FailingAdapter:
        async def execute(self, req):
            raise RuntimeError("Fake Failure")
    
    gateway.registry._adapters["FAILING_CAP"] = FailingAdapter
    req_e = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability="FAILING_CAP")
    res_e = await gateway.execute(req_e, dec_a)
    print(f"TEST E (Adapter failure) -> {res_e.status.value} (Error: {res_e.error_code})")


if __name__ == "__main__":
    asyncio.run(run_manual_verification())
