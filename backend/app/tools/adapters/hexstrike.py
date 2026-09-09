import asyncio
import uuid
import httpx
from datetime import datetime, timezone
from app.schemas.tools import ToolRequest, ToolResult, ToolExecutionState
from app.tools.adapters.base import ToolAdapter
from app.core.config import settings


class HexStrikeAdapter(ToolAdapter):
    """Integrates with the HexStrike REST API for real tool execution."""

    def __init__(self):
        self.base_url = settings.HEXSTRIKE_BASE_URL.rstrip('/')
        self.api_key = settings.HEXSTRIKE_API_KEY
        self.timeout = getattr(settings, "HEXSTRIKE_TIMEOUT_SECONDS", 30)

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def execute(self, request: ToolRequest) -> ToolResult:
        started_at = datetime.now(timezone.utc)
        
        # Determine endpoint based on capability
        # Assuming HexStrike exposes /api/v1/execute
        endpoint = f"{self.base_url}/execute"
        
        payload = {
            "capability": request.capability,
            "target": request.target,
            "parameters": request.parameters
        }
        
        if getattr(request, 'session_context_id', None):
            payload["session_context_id"] = request.session_context_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(endpoint, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                completed_at = datetime.now(timezone.utc)
                duration = int((completed_at - started_at).total_seconds() * 1000)
                
                return ToolResult(
                    execution_id=str(uuid.uuid4()),
                    request_id=request.request_id,
                    capability=request.capability,
                    adapter=self.__class__.__name__,
                    status=ToolExecutionState.SUCCESS,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration,
                    structured_data=data.get("result", {}),
                    output=data.get("output", "")
                )
                
            except httpx.ConnectError:
                return self._build_error_result(
                    request, 
                    ToolExecutionState.UNAVAILABLE, 
                    "HEXSTRIKE_UNAVAILABLE", 
                    "HexStrike service is unreachable or not running.",
                    started_at
                )
            except httpx.TimeoutException:
                return self._build_error_result(
                    request, 
                    ToolExecutionState.TIMEOUT, 
                    "HEXSTRIKE_TIMEOUT", 
                    f"HexStrike timed out after {self.timeout} seconds.",
                    started_at
                )
            except httpx.HTTPStatusError as e:
                # 4xx or 5xx errors
                status_code = e.response.status_code
                error_msg = e.response.text
                return self._build_error_result(
                    request, 
                    ToolExecutionState.FAILED, 
                    f"HEXSTRIKE_HTTP_{status_code}", 
                    f"HexStrike returned HTTP {status_code}: {error_msg}",
                    started_at
                )
            except Exception as e:
                return self._build_error_result(
                    request, 
                    ToolExecutionState.FAILED, 
                    "HEXSTRIKE_EXECUTION_FAILED", 
                    f"Unexpected failure communicating with HexStrike: {str(e)}",
                    started_at
                )

    def _build_error_result(self, request: ToolRequest, state: ToolExecutionState, error_code: str, error_message: str, started_at: datetime) -> ToolResult:
        completed_at = datetime.now(timezone.utc)
        return ToolResult(
            execution_id=str(uuid.uuid4()),
            request_id=request.request_id,
            capability=request.capability,
            adapter=self.__class__.__name__,
            status=state,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=int((completed_at - started_at).total_seconds() * 1000),
            error_code=error_code,
            error_message=error_message
        )
