from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ToolExecutionState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class ToolRequest(BaseModel):
    """A structured request to execute a tool capability."""
    request_id: str
    assessment_id: str
    target: str
    capability: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_by: str = "AresController"
    session_context_id: Optional[str] = None
    policy_decision_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    """A normalized result from a tool adapter."""
    execution_id: str
    request_id: str
    capability: str
    adapter: str
    status: ToolExecutionState
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output: str = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
