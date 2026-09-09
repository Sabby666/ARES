import logging
from app.llm import get_llm_provider
from app.agents.base import BaseAgent, AgentException

logger = logging.getLogger(__name__)

class ObservationAgent(BaseAgent):
    """Agent responsible for evaluating tool results in the VAPT loop."""

    NAME = "ObservationAgent"
    ROLE = "VAPT Result Evaluator"
    DESCRIPTION = "Evaluates the result of a tool execution against the current state."

    def __init__(self):
        super().__init__()
        self.provider = get_llm_provider()

    async def evaluate(self, action: dict, result: dict, state: dict) -> dict:
        """Evaluate observation and return updated finding state/new endpoints."""
        try:
            res = await self.run("evaluate", self._evaluate, action, result, state)
            return res.payload
        except AgentException as ae:
            logger.error(f"ObservationAgent failed: {ae.message}")
            raise RuntimeError(f"Observation evaluation failed: {ae.message}") from ae

    async def _evaluate(self, action: dict, result: dict, state: dict) -> dict:
        logger.info(f"ObservationAgent evaluating result using {self.provider.__class__.__name__}")
        observation = await self.provider.evaluate_observation(action, result, state)
        
        logger.info(f"ObservationAgent determined status: {observation.finding_status}")
        
        return observation.model_dump()
