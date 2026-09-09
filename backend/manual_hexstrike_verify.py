import asyncio
import uuid
import os
from app.tools.gateway import ToolGateway
from app.schemas.tools import ToolRequest
from app.schemas.policy import PolicyDecision, PolicyDecisionResult, ActionCapability
from app.core.config import settings

async def run_manual_verification():
    print("========================================")
    print("MANUAL HEXSTRIKE VERIFICATION RESULTS")
    print("========================================")
    
    os.environ["TOOL_PROVIDER"] = "hexstrike"
    settings.TOOL_PROVIDER = "hexstrike"
    
    gateway = ToolGateway()
    assessment_id = str(uuid.uuid4())
    target = "http://demo.local"

    # TEST A - HexStrike unavailable
    req_a = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target=target, capability=ActionCapability.RECON)
    dec_a = PolicyDecision(decision=PolicyDecisionResult.ALLOW, reason_code="ALLOWED", reason="Test")
    res_a = await gateway.execute(req_a, dec_a)
    print(f"TEST A (HexStrike unavailable) -> {res_a.status.value} (Error: {res_a.error_code})")

    # TEST B - Unauthorized target
    req_b = ToolRequest(request_id=str(uuid.uuid4()), assessment_id=assessment_id, target="https://example.com", capability=ActionCapability.RECON)
    dec_b = PolicyDecision(decision=PolicyDecisionResult.BLOCK, reason_code="BLOCKED_BY_POLICY", reason="Test")
    res_b = await gateway.execute(req_b, dec_b)
    print(f"TEST B (Unauthorized target) -> {res_b.status.value} (Error: {res_b.error_code})")

    # TEST C, D, E are skipped since they require HexStrike to be available
    print(f"TEST C (Allowed local target) -> BLOCKED BY ENVIRONMENT")
    print(f"TEST D (Capability execution) -> BLOCKED BY ENVIRONMENT")
    print(f"TEST E (Result normalization) -> BLOCKED BY ENVIRONMENT")

if __name__ == "__main__":
    asyncio.run(run_manual_verification())
