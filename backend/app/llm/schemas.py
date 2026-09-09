from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CandidateFindingSchema(BaseModel):
    title: str = Field(description="A concise, descriptive title of the vulnerability.")
    category: str = Field(description="The vulnerability category, e.g., 'Injection', 'XSS', 'Broken Access Control'.")
    severity: str = Field(description="Severity level: 'Critical', 'High', 'Medium', 'Low', 'Info'.")
    confidence: float = Field(description="Confidence level between 0.0 and 1.0.")
    endpoint: str = Field(description="The API endpoint or URL path associated with the finding.")
    description: str = Field(description="A detailed description of the vulnerability and its potential impact.")
    reasoning: str = Field(
        description=(
            "Technical reasoning justifying why this is considered a vulnerability, "
            "based solely on the provided recon evidence."
        )
    )
    recommendation: str = Field(description="Suggested remediation steps.")

    # Phase 10 — evidence honesty fields
    evidence_status: Literal["OBSERVED", "INFERRED", "POTENTIAL"] = Field(
        default="POTENTIAL",
        description=(
            "Evidence classification. "
            "OBSERVED = directly seen in recon data; "
            "INFERRED = strongly implied by recon data; "
            "POTENTIAL = plausible but requires validation."
        )
    )
    evidence_requirements: str = Field(
        default="",
        description="What evidence or test result would confirm this finding."
    )
    suggested_validation_context: str = Field(
        default="",
        description="Hint for the ValidationAgent describing how to test this finding."
    )


class AnalysisResultSchema(BaseModel):
    findings: List[CandidateFindingSchema] = Field(
        description="List of candidate findings derived from the recon data."
    )
    analysis_provenance: dict = Field(
        default_factory=dict,
        description=(
            "Source metadata: target, source adapter, execution_mode, timestamp. "
            "Populated by AnalyzerAgent before returning to Controller."
        )
    )


class AttackChainStepSchema(BaseModel):
    step: str = Field(description="Description of the attack step.")


class AttackChainSchema(BaseModel):
    name: str = Field(description="Name of the attack chain.")
    severity: str = Field(description="Overall severity of the attack chain.")
    steps: List[str] = Field(description="Sequential steps to execute the attack chain.")
    findings_involved: List[str] = Field(description="List of finding titles involved in this attack chain.")


class ReasoningResultSchema(BaseModel):
    attack_chains: List[AttackChainSchema] = Field(
        description="Hypothetical multi-step attack chains derived from the findings."
    )
    risk_score: float = Field(description="Overall risk score between 0.0 and 10.0.")
    reasoning_summary: str = Field(description="A markdown-formatted summary report of the analysis.")


# ── VAPT Loop Schemas ─────────────────────────────────────────────────────

class NextActionSchema(BaseModel):
    action_type: str = Field(description="The type of action to perform (e.g., 'explore', 'validate', 'stop')")
    target: str = Field(description="The target URL or domain")
    endpoint: Optional[str] = Field(default=None, description="The specific path or endpoint to target")
    method: Optional[str] = Field(default="GET", description="HTTP method if applicable")
    capability: str = Field(description="The requested ToolRegistry capability (e.g. 'VALIDATION', 'RECON', 'EXPLOITATION', 'BRUTE_FORCE')")
    tool: Optional[str] = Field(default=None, description="The specific tool to use if applicable")
    parameters: dict = Field(default_factory=dict, description="Parameters for the tool execution")
    reason: str = Field(description="Why this action is being proposed based on current evidence")
    expected_observation: str = Field(description="What the agent expects to see if this action is successful")
    risk: str = Field(default="Low", description="Estimated risk of the action (e.g. 'Low', 'High')")
    validation_goal: Optional[str] = Field(default=None, description="The finding or hypothesis this action aims to validate")
    stop_condition: Optional[str] = Field(default=None, description="Condition under which the loop should stop")


class ObservationResultSchema(BaseModel):
    finding_status: Literal["OBSERVED", "HYPOTHESIS", "CANDIDATE", "VALIDATING", "PROVEN", "NOT_PROVEN", "INCONCLUSIVE", "REJECTED"] = Field(
        description="The updated status of the finding based on the tool result."
    )
    analysis: str = Field(description="Analysis of the tool result and whether it confirms the hypothesis.")
    new_endpoints: List[dict] = Field(default_factory=list, description="Any new endpoints discovered during the action.")
    new_technologies: List[dict] = Field(default_factory=list, description="Any new technologies discovered during the action.")


class AttackSurfaceSchema(BaseModel):
    origin: str = Field(default="", description="Where this surface was discovered.")
    path: str = Field(description="The URL path or endpoint.")
    method: str = Field(default="GET", description="HTTP method.")
    parameters: dict = Field(default_factory=dict, description="Query or body parameters.")
    forms: dict = Field(default_factory=dict, description="Forms found on the page.")
    form_fields: dict = Field(default_factory=dict, description="Specific fields within forms.")
    input_fields: dict = Field(default_factory=dict, description="Generic input fields discovered.")
    authentication_required: bool = Field(default=False, description="Whether the endpoint requires authentication.")
    authentication_state: str = Field(default="UNAUTHENTICATED", description="Current authentication state (e.g. UNKNOWN, REQUIRED, AUTHENTICATED).")
    session_context_id: Optional[str] = Field(default=None, description="Identifier for the active session context.")
    csrf_state: dict = Field(default_factory=dict, description="Discovered CSRF tokens or mechanisms.")
    response_status: Optional[int] = Field(default=None, description="Last observed HTTP response status code.")
    response_headers: dict = Field(default_factory=dict, description="Observed HTTP response headers.")
    response_metadata: dict = Field(default_factory=dict, description="Other metadata from the response.")
    technologies: List[str] = Field(default_factory=list, description="Technologies detected.")
    candidate_classes: List[str] = Field(default_factory=list, description="Vulnerability classes that might be relevant.")
    observations: List[str] = Field(default_factory=list, description="Any contextual observations.")
    evidence_refs: List[str] = Field(default_factory=list, description="References to supporting evidence.")


class PentestActionSchema(BaseModel):
    action_type: str = Field(description="The type of action to perform (e.g., 'explore', 'validate', 'stop')")
    target: str = Field(description="The target URL or domain")
    endpoint: Optional[str] = Field(default=None, description="The specific path or endpoint to target")
    method: Optional[str] = Field(default="GET", description="HTTP method if applicable")
    capability: str = Field(description="The requested ToolRegistry capability (e.g. 'VALIDATION', 'COMMAND_INJECTION', 'MISSING_CONTEXT')")
    session_context_id: Optional[str] = Field(default=None, description="Active session context ID, if required.")
    tool: Optional[str] = Field(default=None, description="The specific tool to use if applicable")
    parameters: dict = Field(default_factory=dict, description="Parameters for the tool execution")
    objective: str = Field(description="What this test aims to achieve.")
    hypothesis: str = Field(description="The security hypothesis being tested.")
    reason: str = Field(description="Why this test was chosen.")
    expected_observation: str = Field(description="What the agent expects to see if this test is successful.")
    validation_goal: Optional[str] = Field(default=None, description="The finding title this action aims to validate.")
    policy_requirements: List[str] = Field(default_factory=list, description="Policy constraints to adhere to.")
    risk: str = Field(default="Low", description="Estimated risk of the action (e.g. 'Low', 'High')")
    stop_condition: Optional[str] = Field(default=None, description="Condition under which the loop should stop")

