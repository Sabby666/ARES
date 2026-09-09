import asyncio
import uuid
from datetime import datetime, timezone
from app.schemas.tools import ToolRequest, ToolResult, ToolExecutionState
from app.schemas.policy import PolicyDecision, PolicyDecisionResult
from app.tools.registry import ToolRegistry
from app.core.config import settings

class ToolGateway:
    """
    Orchestrates the safe execution of tools.
    Requires an explicit ALLOW policy decision before invoking any adapter.
    """

    def __init__(self):
        self.registry = ToolRegistry()

    async def execute(self, request: ToolRequest, policy_decision: PolicyDecision) -> ToolResult:
        """Execute a tool request if policy permits, otherwise return BLOCKED."""
        
        # 1. Enforce Policy ALLOW
        if policy_decision.decision != PolicyDecisionResult.ALLOW:
            return self._build_error_result(
                request, 
                state=ToolExecutionState.BLOCKED, 
                error_code="POLICY_NOT_ALLOWED", 
                error_message=f"Tool execution blocked by policy: {policy_decision.reason_code}"
            )
        
        # 2. Resolve capability from registry
        try:
            adapter = self.registry.get_adapter(request.capability)
        except ValueError as e:
            return self._build_error_result(
                request, 
                state=ToolExecutionState.FAILED, 
                error_code="TOOL_NOT_REGISTERED", 
                error_message=str(e)
            )

        # 3. Execute adapter with timeout
        timeout = getattr(settings, "TOOL_TIMEOUT_SECONDS", 30)
        try:
            result = await asyncio.wait_for(adapter.execute(request), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return self._build_error_result(
                request,
                state=ToolExecutionState.TIMEOUT,
                error_code="TOOL_TIMEOUT",
                error_message=f"Tool execution timed out after {timeout} seconds.",
                adapter_name=adapter.__class__.__name__
            )
        except Exception as e:
            # Catch arbitrary unexpected errors
            return self._build_error_result(
                request,
                state=ToolExecutionState.FAILED,
                error_code="TOOL_EXECUTION_FAILED",
                error_message=f"Unexpected failure: {str(e)}",
                adapter_name=adapter.__class__.__name__
            )

    def _build_error_result(self, request: ToolRequest, state: ToolExecutionState, error_code: str, error_message: str, adapter_name: str = "Unknown") -> ToolResult:
        return ToolResult(
            execution_id=str(uuid.uuid4()),
            request_id=request.request_id,
            capability=request.capability,
            adapter=adapter_name,
            status=state,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            error_code=error_code,
            error_message=error_message
        )
