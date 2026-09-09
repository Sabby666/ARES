import asyncio
import logging
import uuid
from typing import List, Dict

from app.core.config import settings
from app.agents.base import BaseAgent
from app.schemas.tools import ToolRequest, ToolExecutionState
from app.tools.gateway import ToolGateway
from app.schemas.policy import PolicyDecision, ActionCapability

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """Validates candidate findings using active tool execution via ToolGateway."""

    NAME = "ValidationAgent"
    ROLE = "Finding Validation"
    DESCRIPTION = "Validates candidate vulnerabilities by sending benign payloads via ToolGateway."

    def __init__(self, tool_gateway: ToolGateway = None):
        super().__init__()
        self._tool_gateway = tool_gateway or ToolGateway()

    async def validate(
        self, 
        target: str, 
        assessment_id: str, 
        policy_decision: PolicyDecision, 
        findings: List[Dict]
    ) -> List[Dict]:
        """Validate each finding actively using the ToolGateway."""
        result = await self.run(
            "validate", 
            self._validate, 
            target, 
            assessment_id, 
            policy_decision, 
            findings
        )
        return result.payload

    async def _validate(
        self, 
        target: str, 
        assessment_id: str, 
        policy_decision: PolicyDecision, 
        findings: List[Dict]
    ) -> List[Dict]:
        validated = []
        for f in findings:
            confidence = f.get("confidence", 0.0)
            
            # Skip validation for very low confidence findings
            if confidence < 0.60:
                f["status"] = "REJECTED"
                validated.append(f)
                continue

            # Build a validation ToolRequest
            val_req = ToolRequest(
                request_id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                target=target,
                capability=ActionCapability.VALIDATION,
                requested_by=self.NAME,
                parameters={
                    "operation": "VERIFY_VULNERABILITY",
                    "category": f.get("category"),
                    "endpoint": f.get("endpoint")
                },
            )
            logger.info(f"[ValidationAgent] Dispatching Validation Request for finding: {f.get('title')}")

            tool_result = await self._tool_gateway.execute(val_req, policy_decision)
            
            if tool_result.status == ToolExecutionState.SUCCESS:
                sd = tool_result.structured_data or {}
                # Assume the adapter returns a boolean "validated" 
                is_validated = sd.get("validated", False)
                if is_validated:
                    f["status"] = "VALIDATED"
                else:
                    f["status"] = "REJECTED"
            else:
                logger.warning(f"[ValidationAgent] Validation tool execution failed or blocked: {tool_result.status}")
                f["status"] = "NEEDS_REVIEW"

            # Attach the specific validation evidence to this finding
            f["evidence_data"] = tool_result
            validated.append(f)

        return validated
