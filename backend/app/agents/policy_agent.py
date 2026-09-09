# backend/app/agents/policy_agent.py
"""Policy Agent — enforces target-scope rules before any scan starts."""

import asyncio
from app.core.config import settings
from app.policy.gateway import PolicyGateway
from app.schemas.policy import PolicyAction, PolicyDecision
from app.agents.base import BaseAgent


class PolicyAgent(BaseAgent):
    """Enforces target-scope rules before any action executes using PolicyGateway."""

    NAME = "PolicyAgent"
    ROLE = "Policy & Governance"
    DESCRIPTION = "Validates actions against allowed scope before assessment begins. Blocks disallowed actions."

    def __init__(self):
        super().__init__()
        self.gateway = PolicyGateway()

    async def evaluate_action(self, action: PolicyAction, assessment) -> PolicyDecision:
        """Evaluate a proposed policy action using the agent framework."""
        result = await self.run("evaluate_action", self._evaluate, action, assessment)
        return result.payload

    async def _evaluate(self, action: PolicyAction, assessment) -> PolicyDecision:
        await asyncio.sleep(settings.DELAY_POLICY_MS / 1000)
        return self.gateway.evaluate(action, assessment)
