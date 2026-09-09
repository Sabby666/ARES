import logging
from app.llm import get_llm_provider
from app.agents.base import BaseAgent, AgentException

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """Agent responsible for planning the next action in the VAPT loop."""

    NAME = "PlannerAgent"
    ROLE = "VAPT Action Planner"
    DESCRIPTION = "Evaluates current assessment state and proposes the next targeted action."

    def __init__(self):
        super().__init__()
        self.provider = get_llm_provider()

    async def plan(self, state: dict) -> dict:
        """Propose the next action based on current state."""
        try:
            result = await self.run("plan", self._plan, state)
            return result.payload
        except AgentException as ae:
            logger.error(f"PlannerAgent failed: {ae.message}")
            raise RuntimeError(f"Planning failed: {ae.message}") from ae

    async def _plan(self, state: dict) -> dict:
        logger.info(f"PlannerAgent generating next action using {self.provider.__class__.__name__}")
        next_action = await self.provider.plan_next_action(state)
        
        logger.info(f"PlannerAgent proposed action: {next_action.action_type} - {next_action.capability}")
        
        return next_action.model_dump()
