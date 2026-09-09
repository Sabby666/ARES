from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ActionCapability(str, Enum):
    """Allowed capabilities that the agents can propose."""
    RECON = "RECON"
    DISCOVERY = "DISCOVERY"
    HTTP_ANALYSIS = "HTTP_ANALYSIS"
    VULNERABILITY_ANALYSIS = "VULNERABILITY_ANALYSIS"
    VALIDATION = "VALIDATION"
    EXPLOITATION = "EXPLOITATION"
    BRUTE_FORCE = "BRUTE_FORCE"
    # M4 Granular Capabilities
    COMMAND_INJECTION = "COMMAND_INJECTION"
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    AUTHENTICATION_TEST = "AUTHENTICATION_TEST"


class PolicyAction(BaseModel):
    """A proposed action submitted to the Policy Gateway for evaluation."""
    action_id: str
    assessment_id: str
    target: str
    action_type: str = Field(..., description="High level action name (e.g. endpoint_scan)")
    capability: str  # Kept as str to allow invalid capabilities to be caught by the engine, not Pydantic validation failure.
    endpoint: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_by: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyDecisionResult(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class PolicyDecision(BaseModel):
    """The result of a policy gateway evaluation."""
    decision: PolicyDecisionResult
    reason_code: str
    reason: str
    audit_id: Optional[str] = None
