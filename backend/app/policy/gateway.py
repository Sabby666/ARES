import uuid
from urllib.parse import urlparse
from app.core.config import settings
from app.models.models import Assessment
from app.schemas.policy import PolicyAction, PolicyDecision, PolicyDecisionResult, ActionCapability


class PolicyGateway:
    """
    The definitive Policy Enforcement boundary.
    Evaluates proposed PolicyActions deterministically.
    """

    def _normalize_target(self, target: str) -> str:
        """Extract the hostname safely from a target string."""
        normalized = target.strip().lower()
        if "://" in normalized:
            parsed = urlparse(normalized)
            return parsed.hostname or ""
        return normalized.split("/")[0].split(":")[0]

    def _check_target_allowed(self, hostname: str) -> bool:
        """Check against the ALLOWED_TARGETS in configuration."""
        # Using a hardcoded list for safety per prototype rules, or falling back to settings
        # The prompt says: "Only if those values already exist in the project's configuration."
        allowed_hosts = set([self._normalize_target(t) for t in settings.ALLOWED_TARGETS])
        # Include defaults just in case
        allowed_hosts.update({"localhost", "127.0.0.1", "demo.local"})
        return hostname in allowed_hosts

    def evaluate(self, action: PolicyAction, assessment: Assessment) -> PolicyDecision:
        """Evaluate a proposed action and return a structured decision."""

        # 1. Assessment exists & State valid
        if not assessment:
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="ASSESSMENT_NOT_FOUND",
                reason="The assessment could not be found."
            )

        active_states = {"CREATED", "POLICY_CHECK", "RECON", "ANALYSIS", "LLM_REASONING", "VALIDATION"}
        if assessment.status not in active_states:
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="ASSESSMENT_NOT_ACTIVE",
                reason=f"Assessment is in state '{assessment.status}' and cannot accept new actions."
            )

        # 2. Target present and allowed
        if not action.target:
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="TARGET_MISSING",
                reason="No target was provided in the action."
            )

        action_hostname = self._normalize_target(action.target)
        if not self._check_target_allowed(action_hostname):
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="TARGET_NOT_ALLOWED",
                reason=f"Target '{action_hostname}' is outside the configured authorized target list."
            )

        # 3. Scope Valid (action target matches assessment target)
        assessment_hostname = self._normalize_target(assessment.target)
        if action_hostname != assessment_hostname:
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="TARGET_OUTSIDE_SCOPE",
                reason=f"Action target '{action_hostname}' does not match assessment target '{assessment_hostname}'."
            )

        # Ensure endpoint is within scope if provided
        if action.endpoint:
            ep_hostname = self._normalize_target(action.endpoint)
            # If endpoint is a full URL with a host, it must match the authorized target
            if ep_hostname and ep_hostname != assessment_hostname and ep_hostname not in ["", None]:
                return PolicyDecision(
                    decision=PolicyDecisionResult.BLOCK,
                    reason_code="ENDPOINT_OUTSIDE_SCOPE",
                    reason=f"Endpoint '{action.endpoint}' points to a different host."
                )

        # 4. Capability allowed
        try:
            # Pydantic may have allowed string through, check if it's a valid enum
            ActionCapability(action.capability)
        except ValueError:
            return PolicyDecision(
                decision=PolicyDecisionResult.BLOCK,
                reason_code="CAPABILITY_NOT_ALLOWED",
                reason=f"Capability '{action.capability}' is unknown or disallowed."
            )

        # 5. Parameters valid
        for key, value in action.parameters.items():
            str_val = str(value).lower()
            if "bash " in str_val or "sh -c" in str_val or "cmd.exe" in str_val:
                return PolicyDecision(
                    decision=PolicyDecisionResult.BLOCK,
                    reason_code="ARBITRARY_EXECUTION_DETECTED",
                    reason="Arbitrary shell execution strings detected in parameters."
                )

        # If we passed all checks, ALLOW
        return PolicyDecision(
            decision=PolicyDecisionResult.ALLOW,
            reason_code="ACTION_ALLOWED",
            reason="Action conforms to all policy constraints.",
            audit_id=str(uuid.uuid4())
        )
