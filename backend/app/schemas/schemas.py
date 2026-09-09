# backend/app/schemas/schemas.py
"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ── Generic response wrapper ─────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""


class APIError(BaseModel):
    success: bool = False
    error: dict = Field(default_factory=lambda: {"code": "UNKNOWN", "message": "An error occurred"})


# ── Assessment ────────────────────────────────────────────────────────────

class AssessmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target: str = Field(..., min_length=1, max_length=512)
    scope: str = Field(default="", max_length=512)
    description: str = Field(default="", max_length=2000)
    project_id: Optional[str] = None


class AssessmentOut(BaseModel):
    id: str
    project_id: str
    name: str
    target: str
    scope: str
    description: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    recon_data: Optional[dict] = None
    analysis_data: Optional[dict] = None
    reasoning_data: Optional[dict] = None
    findings_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentListOut(BaseModel):
    id: str
    name: str
    target: str
    status: str
    findings_count: int = 0
    validation_summary: str = ""
    execution_mode: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Evidence ──────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    id: str
    assessment_id: str
    finding_id: Optional[str] = None
    agent: str
    action: str
    evidence_type: str
    content: str
    source: str
    source_type: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Finding ───────────────────────────────────────────────────────────────

class FindingOut(BaseModel):
    id: str
    assessment_id: str
    title: str
    category: str
    severity: str
    confidence: float
    endpoint: str
    description: str
    reasoning: str
    recommendation: str
    status: str
    agent: str
    finding_signature: Optional[str] = None
    evidence_data: Optional[Any] = None
    evidence: List[EvidenceOut] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Activity ──────────────────────────────────────────────────────────────

class ActivityOut(BaseModel):
    id: str
    assessment_id: str
    agent: str
    message: str
    log_type: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Report ────────────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    id: str
    assessment_id: str
    report_type: str
    content: str
    findings_count: int
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_assessments: int = 0
    running: int = 0
    completed: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    total_evidence: int = 0


class DashboardOut(BaseModel):
    stats: DashboardStats
    recent_assessments: List[AssessmentListOut] = []


# ── Agent ─────────────────────────────────────────────────────────────────

class AgentInfo(BaseModel):
    name: str
    role: str
    description: str
    status: str = "ready"
    last_action: str = ""
    actions_executed: int = 0


# ── Tool ──────────────────────────────────────────────────────────────────

class ToolInfo(BaseModel):
    id: str = ""
    name: str
    description: str
    tool_type: str
    safe: bool = True


# ── VAPT Loop ─────────────────────────────────────────────────────────────

class NextAction(BaseModel):
    """Structured action proposed by the PlannerAgent."""
    action_type: str = Field(description="The type of action to perform (e.g., 'explore', 'validate', 'stop')")
    target: str = Field(description="The target URL or domain")
    endpoint: Optional[str] = Field(default=None, description="The specific path or endpoint to target")
    method: Optional[str] = Field(default="GET", description="HTTP method if applicable")
    capability: str = Field(description="The requested ToolRegistry capability (e.g. 'VALIDATION', 'COMMAND_INJECTION', 'MISSING_CONTEXT')")
    session_context_id: Optional[str] = Field(default=None, description="Active session context ID, if required.")
    tool: Optional[str] = Field(default=None, description="The specific tool to use if applicable")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool execution")
    reason: str = Field(description="Why this action is being proposed based on current evidence")
    expected_observation: str = Field(description="What the agent expects to see if this action is successful")
    risk: str = Field(default="Low", description="Estimated risk of the action (e.g. 'Low', 'High')")
    validation_goal: Optional[str] = Field(default=None, description="The finding or hypothesis this action aims to validate")
    stop_condition: Optional[str] = Field(default=None, description="Condition under which the loop should stop")


class AssessmentState(BaseModel):
    """A living representation of the attack surface and findings during the VAPT loop."""
    assessment_id: str
    target: str
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    technologies: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    actions_taken: int = 0
    max_actions: int = 10
    recent_observations: List[str] = Field(default_factory=list)
    status: str = "IN_PROGRESS"

