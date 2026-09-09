# backend/app/agents/analyzer_agent.py
"""
Analyzer Agent — Phase 10.

Accepts a typed ReconResult from Phase 9 and produces candidate vulnerability
findings via the LLMProvider abstraction. Never calls httpx, shell, or adapters
directly.

Data path:
    ReconResult → AnalyzerAgent → LLMProvider → AnalysisResultSchema
                                              → list[dict] (to Controller)
"""

import logging
from datetime import datetime, timezone

from app.agents.base import BaseAgent, AgentException
from app.llm import get_llm_provider
from app.llm.schemas import AnalysisResultSchema
from app.schemas.recon import ReconResult

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Analyzes a typed ReconResult and generates candidate security findings
    using an LLMProvider.

    Responsibilities:
    - Accept a ReconResult (Phase 9 schema), not a raw dict.
    - Build a recon_data dict for the LLMProvider from ReconResult fields.
    - Invoke LLMProvider.analyze_recon_data().
    - Annotate each finding with evidence_status, agent, status.
    - Return a list[dict] for the Controller — no DB writes.

    NOT responsible for:
    - Network or shell execution
    - Database persistence (Controller owns that)
    - Policy evaluation
    - Validation (ValidationAgent owns that)
    """

    NAME = "AnalyzerAgent"
    ROLE = "Vulnerability Analysis"
    DESCRIPTION = (
        "Examines Phase 9 ReconResult data via LLMProvider to identify "
        "candidate security vulnerabilities with evidence honesty tags."
    )

    def __init__(self, provider=None):
        super().__init__()
        self.provider = provider or get_llm_provider()

    async def analyze(self, recon_result: ReconResult) -> list[dict]:
        """
        Analyze a typed ReconResult and return candidate findings.

        Parameters
        ----------
        recon_result : ReconResult
            The structured output from Phase 9 ReconAgent.

        Returns
        -------
        list[dict]
            Serialised CandidateFindingSchema dicts, each annotated with
            status=CANDIDATE and agent=AnalyzerAgent. Ready for Controller
            to pass to LLMReasoner and ValidationAgent.
        """
        try:
            result = await self.run("analyze", self._analyze, recon_result)
            return result.payload
        except AgentException as ae:
            logger.error(f"AnalyzerAgent analysis failed: {ae.message}")
            raise RuntimeError(f"LLM Analysis failed: {ae.message}") from ae

    async def _analyze(self, recon_result: ReconResult) -> list[dict]:
        logger.info(
            f"AnalyzerAgent starting analysis for target={recon_result.target} "
            f"using {self.provider.__class__.__name__} "
            f"[mode={recon_result.execution_mode.value}]"
        )

        # Build the recon_data dict that the LLMProvider contract expects.
        # This is derived exclusively from the typed ReconResult — no hardcoding.
        recon_data = recon_result.to_controller_dict()

        # Invoke LLMProvider (MockProvider or OmniRouteProvider)
        analysis_result: AnalysisResultSchema = await self.provider.analyze_recon_data(
            recon_data
        )

        # Attach provenance from the ReconResult to the AnalysisResultSchema
        analysis_result.analysis_provenance = {
            "target": recon_result.target,
            "source": recon_result.source,
            "execution_mode": recon_result.execution_mode.value,
            "tool_execution_reference": recon_result.tool_execution_reference,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "provider": self.provider.__class__.__name__,
        }

        # Serialize findings and annotate for Controller
        findings = []
        for f in analysis_result.findings:
            finding = f.model_dump()
            finding["status"] = "CANDIDATE"
            finding["agent"] = self.NAME
            findings.append(finding)

        logger.info(
            f"AnalyzerAgent generated {len(findings)} candidate findings "
            f"[provider={self.provider.__class__.__name__}]"
        )
        return findings
