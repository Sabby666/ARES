import asyncio
from typing import Any, Dict, List

from .provider import LLMProvider
from .schemas import (
    AnalysisResultSchema,
    CandidateFindingSchema,
    ReasoningResultSchema,
    AttackChainSchema,
)
from app.core.config import settings


class MockProvider(LLMProvider):
    """
    Offline mock provider — returns deterministic data derived from the
    actual recon_data input.

    Rules:
    - Never ignores recon_data; reads observations, endpoints, headers.
    - Each finding references real input signals, not hardcoded fixture strings.
    - All findings carry proper evidence_status, evidence_requirements,
      and suggested_validation_context (Phase 10 requirements).
    - No external calls.
    """

    async def analyze_recon_data(self, recon_data: Dict[str, Any]) -> AnalysisResultSchema:
        await asyncio.sleep(settings.DELAY_ANALYSIS_MS / 1000)

        findings: List[CandidateFindingSchema] = []
        endpoints = recon_data.get("endpoints", [])
        headers = recon_data.get("headers", {})
        observations = recon_data.get("observations", [])
        technologies = recon_data.get("technologies", [])
        target = recon_data.get("target", "(unknown)")
        execution_mode = recon_data.get("execution_mode", "SIMULATED")

        # ── Finding 1: .env exposure (from endpoint list) ────────────────────
        env_endpoint = next(
            (ep for ep in endpoints if ep.get("path") == "/.env"), None
        )
        if env_endpoint or any(".env" in obs for obs in observations):
            evidence_st = "OBSERVED" if env_endpoint else "INFERRED"
            findings.append(
                CandidateFindingSchema(
                    title="Sensitive File Exposure — .env",
                    category="Information Disclosure",
                    severity="Critical",
                    confidence=0.96,
                    endpoint="/.env",
                    description=(
                        f"The .env configuration file is publicly accessible on {target}. "
                        "This file commonly contains database credentials, API keys, "
                        "and secret tokens."
                    ),
                    reasoning=(
                        f"Endpoint /.env returned HTTP "
                        f"{env_endpoint.get('status', '?') if env_endpoint else 'unknown'} "
                        "in the recon data. Observation signals also confirm exposure."
                        if env_endpoint else
                        "Recon observation explicitly notes .env exposure."
                    ),
                    recommendation=(
                        "Deny all HTTP access to dotfiles via web server configuration. "
                        "Rotate any credentials that may have been exposed."
                    ),
                    evidence_status=evidence_st,
                    evidence_requirements=(
                        "Confirm that /.env returns a 200 response with readable "
                        "environment variable content."
                    ),
                    suggested_validation_context=(
                        "Issue a GET request to /.env and verify the response body "
                        "contains KEY=VALUE pairs."
                    ),
                )
            )

        # ── Finding 2: Missing security headers (from headers dict) ─────────
        missing_headers = [
            k for k, v in headers.items()
            if isinstance(v, str) and v.upper() == "MISSING"
        ]
        if missing_headers:
            findings.append(
                CandidateFindingSchema(
                    title="Missing HTTP Security Headers",
                    category="Security Misconfiguration",
                    severity="Medium",
                    confidence=0.95,
                    endpoint="/",
                    description=(
                        f"The following security headers are absent on {target}: "
                        f"{', '.join(missing_headers)}. "
                        "Their absence leaves users exposed to clickjacking, "
                        "MIME-sniffing, and injection attacks."
                    ),
                    reasoning=(
                        f"Recon headers show {', '.join(missing_headers)} as MISSING. "
                        "These are directly OBSERVED in the captured HTTP response headers."
                    ),
                    recommendation=(
                        "Configure the web server to emit all recommended security headers. "
                        "Use securityheaders.com to validate."
                    ),
                    evidence_status="OBSERVED",
                    evidence_requirements=(
                        "Confirm that an HTTP response to / lacks the headers listed above."
                    ),
                    suggested_validation_context=(
                        "Issue a GET request to / and inspect the response headers "
                        "for the absent fields."
                    ),
                )
            )

        # ── Finding 3: Server version disclosure (from Server header) ────────
        server_header = headers.get("Server", "")
        if server_header and server_header.upper() != "MISSING":
            findings.append(
                CandidateFindingSchema(
                    title="Server Version Disclosure",
                    category="Information Disclosure",
                    severity="Low",
                    confidence=0.97,
                    endpoint="/",
                    description=(
                        f"The Server response header on {target} reveals the software "
                        f"and version: '{server_header}'. Attackers can use this to "
                        "target known CVEs."
                    ),
                    reasoning=(
                        f"HTTP response headers directly expose '{server_header}'. "
                        "This is an OBSERVED signal from the recon data."
                    ),
                    recommendation=(
                        "Remove or obfuscate the Server header in web server configuration."
                    ),
                    evidence_status="OBSERVED",
                    evidence_requirements=(
                        "Confirm that an HTTP response includes a Server header "
                        "with a version string."
                    ),
                    suggested_validation_context=(
                        "Issue a HEAD or GET request to / and read the Server header."
                    ),
                )
            )

        # ── Finding 4: Admin endpoint accessible (from endpoint list) ────────
        admin_ep = next(
            (ep for ep in endpoints
             if "admin" in ep.get("path", "").lower()
             and ep.get("status") not in (401, 403)),
            None,
        )
        if admin_ep:
            findings.append(
                CandidateFindingSchema(
                    title="Admin Endpoint Accessible Without Authorization",
                    category="Broken Access Control",
                    severity="High",
                    confidence=0.80,
                    endpoint=admin_ep.get("path", "/api/admin"),
                    description=(
                        f"An administrative endpoint at {admin_ep.get('path')} returned "
                        f"HTTP {admin_ep.get('status')} (not 401/403) during recon. "
                        "This may indicate missing authentication enforcement."
                    ),
                    reasoning=(
                        f"Endpoint {admin_ep.get('path')} returned "
                        f"HTTP {admin_ep.get('status')} during the recon scan. "
                        "A non-error response to an admin path without credentials "
                        "strongly implies access control is not enforced."
                    ),
                    recommendation=(
                        "Require authentication and authorization checks on all "
                        "administrative endpoints. Apply the principle of least privilege."
                    ),
                    evidence_status="INFERRED",
                    evidence_requirements=(
                        "Confirm the endpoint returns sensitive data without a valid "
                        "session cookie or Authorization header."
                    ),
                    suggested_validation_context=(
                        f"Issue a GET request to {admin_ep.get('path')} without "
                        "authentication credentials and verify the response content."
                    ),
                )
            )

        # ── Finding 5: Technology-inferred findings (POTENTIAL) ──────────────
        tech_names = {t.get("name", "").lower() for t in technologies}
        if "jwt" in tech_names:
            findings.append(
                CandidateFindingSchema(
                    title="JWT Implementation — Potential Algorithm Confusion",
                    category="Broken Authentication",
                    severity="High",
                    confidence=0.45,
                    endpoint="/login",
                    description=(
                        f"Target {target} uses JWT for authentication. "
                        "JWT implementations are susceptible to algorithm confusion "
                        "attacks (e.g., RS256→HS256 downgrade) if not properly configured."
                    ),
                    reasoning=(
                        "Technology stack includes JWT. Algorithm confusion is a "
                        "well-known class of JWT vulnerability but cannot be confirmed "
                        "without active testing."
                    ),
                    recommendation=(
                        "Explicitly set the allowed algorithm in the JWT library "
                        "configuration. Reject tokens with the 'none' algorithm."
                    ),
                    evidence_status="POTENTIAL",
                    evidence_requirements=(
                        "Attempt to forge a token using HS256 signed with the server's "
                        "public key; confirm if the server accepts it."
                    ),
                    suggested_validation_context=(
                        "Craft a modified JWT with the algorithm header changed to HS256 "
                        "and submit to a protected endpoint."
                    ),
                )
            )

        return AnalysisResultSchema(
            findings=findings,
            analysis_provenance={
                "target": target,
                "source": recon_data.get("source", "MockReconAdapter"),
                "execution_mode": execution_mode,
                "findings_generated": len(findings),
                "provider": "MockProvider",
            },
        )

    async def reason_about_findings(
        self, findings: List[Dict[str, Any]], recon_data: Dict[str, Any]
    ) -> ReasoningResultSchema:
        await asyncio.sleep(settings.DELAY_LLM_MS / 1000)

        target = recon_data.get("target", "(unknown)")

        # Build attack chains from actual finding titles in the input
        finding_titles = [f.get("title", "") for f in findings]
        env_title = next((t for t in finding_titles if ".env" in t), None)
        admin_title = next((t for t in finding_titles if "Admin" in t), None)

        attack_chains = []
        if env_title and admin_title:
            attack_chains.append(
                AttackChainSchema(
                    name="Credential Exposure → Admin Access",
                    severity="Critical",
                    steps=[
                        f"Read {env_title} to extract DB credentials",
                        "Use credentials against the admin endpoint",
                        "Escalate access to internal configuration",
                    ],
                    findings_involved=[env_title, admin_title],
                )
            )
        elif env_title:
            attack_chains.append(
                AttackChainSchema(
                    name="Information Disclosure → Credential Theft",
                    severity="Critical",
                    steps=[
                        "Read .env file to obtain credentials",
                        "Use credentials to access internal systems",
                    ],
                    findings_involved=[env_title],
                )
            )
        else:
            attack_chains.append(
                AttackChainSchema(
                    name="Security Misconfiguration → Information Gathering",
                    severity="Medium",
                    steps=[
                        "Exploit missing security headers to gather information",
                        "Use gathered information for targeted attacks",
                    ],
                    findings_involved=finding_titles[:2] if finding_titles else [],
                )
            )

        risk_score = min(
            10.0,
            sum(
                {"Critical": 9.0, "High": 7.0, "Medium": 5.0, "Low": 2.0, "Info": 0.5}.get(
                    f.get("severity", "Low"), 1.0
                ) * f.get("confidence", 0.5)
                for f in findings
            ) / max(len(findings), 1),
        )

        severity_line = (
            f"Highest severity findings: "
            f"{', '.join(set(f.get('severity','?') for f in findings[:3]))}"
            if findings else "No findings."
        )
        reasoning_summary = (
            f"## ARES LLM Reasoning Report (Mock)\n\n"
            f"**Target**: {target}\n\n"
            f"{severity_line}\n\n"
            f"**Risk Score**: {risk_score:.1f}/10  \n"
            f"**Attack Chains Identified**: {len(attack_chains)}\n\n"
            f"*Note: This is a simulated analysis from MockProvider. "
            f"Results reflect recon data signals only.*"
        )

        return ReasoningResultSchema(
            attack_chains=attack_chains,
            risk_score=round(risk_score, 2),
            reasoning_summary=reasoning_summary,
        )

    async def plan_next_action(self, state: Dict[str, Any]) -> "PentestActionSchema":
        from .schemas import PentestActionSchema
        await asyncio.sleep(settings.DELAY_LLM_MS / 1000)

        findings = state.get("findings", [])
        candidate = next((f for f in findings if f.get("status") in ("HYPOTHESIS", "CANDIDATE")), None)

        if candidate:
            return PentestActionSchema(
                action_type="validate",
                target=state.get("target", "unknown"),
                endpoint=candidate.get("endpoint"),
                capability="VALIDATION",
                reason=f"Attempting to validate hypothesis: {candidate.get('title')}",
                objective="Prove vulnerability exists",
                hypothesis=candidate.get("title", ""),
                expected_observation="Confirmation of vulnerability in tool output",
                validation_goal=candidate.get("title")
            )
        
        # Default stop
        return PentestActionSchema(
            action_type="stop",
            target=state.get("target", "unknown"),
            capability="NONE",
            reason="No more hypotheses to validate.",
            objective="Stop the loop",
            hypothesis="",
            expected_observation="End of assessment"
        )

    async def evaluate_observation(self, action: Dict[str, Any], result: Dict[str, Any], state: Dict[str, Any]) -> "ObservationResultSchema":
        from .schemas import ObservationResultSchema
        await asyncio.sleep(settings.DELAY_LLM_MS / 1000)
        
        status = "PROVEN" if result.get("status") == "SUCCESS" else "NOT_PROVEN"
        
        return ObservationResultSchema(
            finding_status=status,
            analysis=f"Mock evaluation determined {status} based on tool result status: {result.get('status')}",
            new_endpoints=[],
            new_technologies=[]
        )
