# backend/app/agents/llm_reasoner.py
"""LLM Reasoner Agent — simulates LLM-powered reasoning and prioritization."""

import logging
from app.llm import get_llm_provider
from app.agents.base import BaseAgent, AgentException

logger = logging.getLogger(__name__)


class LLMReasoner(BaseAgent):
    """LLM reasoner that enriches findings with reasoning chains using an LLM provider."""

    NAME = "LLMReasoner"
    ROLE = "LLM Reasoning & Prioritization"
    DESCRIPTION = "Applies chain-of-thought reasoning to prioritize findings, assess exploitability, and suggest attack chains."

    def __init__(self):
        super().__init__()
        self.provider = get_llm_provider()

    async def reason(self, findings: list[dict], recon_data: dict) -> dict:
        """Apply LLM reasoning to findings using the agent framework."""
        try:
            result = await self.run("reason", self._reason, findings, recon_data)
            return result.payload
        except AgentException as ae:
            logger.error(f"LLMReasoner reasoning failed: {ae.message}")
            raise RuntimeError(f"LLM Reasoning failed: {ae.message}") from ae

    async def _reason(self, findings: list[dict], recon_data: dict) -> dict:
        logger.info(f"LLMReasoner starting reasoning using {self.provider.__class__.__name__}")
        reasoning_result = await self.provider.reason_about_findings(findings, recon_data)
        
        SEVERITY_WEIGHTS = {
            "Critical": 10,
            "High": 7,
            "Medium": 4,
            "Low": 2,
            "Info": 1,
        }
        
        scored = []
        for f in findings:
            w = SEVERITY_WEIGHTS.get(f.get("severity", "Info"), 1)
            c = f.get("confidence", 0.5)
            scored.append((w * c, f))
        scored.sort(key=lambda x: x[0], reverse=True)
        prioritized = [f for _, f in scored]
        
        logger.info("LLMReasoner generated attack chains and risk score")
        
        return {
            "prioritized_findings": prioritized,
            "attack_chains": [chain.model_dump() for chain in reasoning_result.attack_chains],
            "reasoning_summary": reasoning_result.reasoning_summary,
            "risk_score": reasoning_result.risk_score,
            "model": self.provider.__class__.__name__,
        }
