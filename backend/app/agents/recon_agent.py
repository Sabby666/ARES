# backend/app/agents/recon_agent.py
"""
Reconnaissance Agent — Phase 9.
All recon data is produced by the ToolGateway → ToolAdapter chain.
ReconAgent does not own mock data, does not call adapters directly,
and does not perform any network or shell operations.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.agents.base import BaseAgent, AgentException
from app.schemas.recon import (
    ReconResult, ReconExecutionMode, ReconEndpoint, ReconTechnology,
)
from app.schemas.tools import ToolRequest, ToolResult, ToolExecutionState
from app.schemas.policy import ActionCapability, PolicyDecision
from app.tools.gateway import ToolGateway

logger = logging.getLogger(__name__)


class ReconAgent(BaseAgent):
    """
    Reconnaissance agent that delegates all tool execution to ToolGateway.

    Responsibilities:
    - Build a structured ToolRequest for the RECON capability
    - Invoke ToolGateway.execute() with the authorized PolicyDecision
    - Parse and validate the ToolResult into a typed ReconResult
    - Surface structured failures / timeouts to the Controller

    NOT responsible for:
    - Mock data generation (owned by MockReconAdapter)
    - Network/shell access (owned by adapters behind ToolGateway)
    - Policy evaluation (owned by PolicyGateway/PolicyAgent)
    """

    NAME = "ReconAgent"
    ROLE = "Reconnaissance"
    DESCRIPTION = (
        "Discovers endpoints, technologies, and attack surface via "
        "the ToolGateway → ToolAdapter boundary."
    )

    def __init__(self, tool_gateway: ToolGateway = None):
        super().__init__()
        self._tool_gateway = tool_gateway or ToolGateway()

    async def scan(
        self,
        target: str,
        assessment_id: str,
        policy_decision: PolicyDecision,
    ) -> ReconResult:
        """
        Execute recon for an authorized target.

        Parameters
        ----------
        target:          The authorized target string from the assessment.
        assessment_id:   Assessment context for ToolRequest correlation.
        policy_decision: The ALLOW decision from PolicyGateway. Must be ALLOW.

        Returns
        -------
        ReconResult — always structured, never raises except on programming errors.
        """
        try:
            result = await self.run(
                "scan",
                self._scan,
                target,
                assessment_id,
                policy_decision,
            )
            return result.payload
        except AgentException as ae:
            logger.error(f"ReconAgent scan failed: {ae.message}")
            raise RuntimeError(f"Recon failed: {ae.message}") from ae

    async def _scan(
        self,
        target: str,
        assessment_id: str,
        policy_decision: PolicyDecision,
    ) -> ReconResult:
        # 1. Build the ToolRequest
        recon_req = ToolRequest(
            request_id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            target=target,
            capability=ActionCapability.RECON,
            requested_by=self.NAME,
            parameters={"operation": "DISCOVER_ENDPOINTS"},
        )
        logger.info(f"[ReconAgent] Dispatching ToolRequest for target={target}")

        # 2. Invoke ToolGateway (never call adapters directly)
        tool_result: ToolResult = await self._tool_gateway.execute(
            recon_req, policy_decision
        )
        logger.info(
            f"[ReconAgent] ToolResult received: status={tool_result.status}, "
            f"adapter={tool_result.adapter}, execution_id={tool_result.execution_id}"
        )

        # 3. Parse ToolResult → ReconResult
        return self._parse_tool_result(tool_result, target)

    def _parse_tool_result(self, tool_result: ToolResult, target: str) -> ReconResult:
        """
        Parse a ToolResult into a validated ReconResult.
        Handles all terminal states; never fabricates data on failure.
        """
        sd = tool_result.structured_data or {}

        if tool_result.status == ToolExecutionState.SUCCESS:
            return self._build_success_result(tool_result, sd, target)

        if tool_result.status == ToolExecutionState.BLOCKED:
            raise RuntimeError(
                f"Recon blocked by policy: {tool_result.error_code} — {tool_result.error_message}"
            )

        if tool_result.status == ToolExecutionState.TIMEOUT:
            raise RuntimeError(
                f"Recon timed out: {tool_result.error_code} — {tool_result.error_message}"
            )

        if tool_result.status in (ToolExecutionState.FAILED, ToolExecutionState.UNAVAILABLE):
            raise RuntimeError(
                f"Recon tool failed: {tool_result.error_code} — {tool_result.error_message}"
            )

        # Malformed / unexpected status
        raise RuntimeError(
            f"Recon returned unexpected status '{tool_result.status}'. "
            f"No data fabricated."
        )

    def _build_success_result(
        self, tool_result: ToolResult, sd: dict, target: str
    ) -> ReconResult:
        """
        Map the adapter's structured_data onto a typed ReconResult.
        Does not invent missing fields — defaults to safe empty values.
        """
        # Determine execution mode from adapter metadata
        meta = tool_result.metadata or {}
        raw_mode = meta.get("execution_mode") or sd.get("execution_mode", "SIMULATED")
        try:
            exec_mode = ReconExecutionMode(raw_mode.upper())
        except ValueError:
            exec_mode = ReconExecutionMode.SIMULATED

        # Parse endpoints safely
        endpoints = []
        for ep in sd.get("endpoints", []):
            try:
                endpoints.append(ReconEndpoint(**ep))
            except Exception:
                # Log malformed entry but don't fail the whole result
                logger.warning(f"[ReconAgent] Skipping malformed endpoint entry: {ep}")

        # Parse technologies safely
        technologies = []
        for tech in sd.get("technologies", []):
            try:
                technologies.append(ReconTechnology(**tech))
            except Exception:
                logger.warning(f"[ReconAgent] Skipping malformed technology entry: {tech}")

        return ReconResult(
            target=sd.get("target", target),
            source=meta.get("source") or sd.get("source") or tool_result.adapter,
            execution_mode=exec_mode,
            tool_execution_reference=tool_result.execution_id,
            reachable=sd.get("reachable", True),
            status_code=sd.get("status_code"),
            endpoints_discovered=sd.get("endpoints_discovered", len(endpoints)),
            endpoints=endpoints,
            technologies=technologies,
            headers=sd.get("headers", {}),
            open_ports=sd.get("open_ports", []),
            dns_records=sd.get("dns_records", []),
            tls=sd.get("tls"),
            observations=sd.get("observations", []),
            timestamp=tool_result.completed_at or datetime.now(timezone.utc),
        )
