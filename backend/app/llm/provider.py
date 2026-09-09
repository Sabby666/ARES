from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .schemas import AnalysisResultSchema, ReasoningResultSchema

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def analyze_recon_data(self, recon_data: Dict[str, Any]) -> AnalysisResultSchema:
        """
        Analyze recon data and extract candidate vulnerabilities.
        Must return structured output according to AnalysisResultSchema.
        """
        pass

    @abstractmethod
    async def reason_about_findings(self, findings: List[Dict[str, Any]], recon_data: Dict[str, Any]) -> ReasoningResultSchema:
        """
        Prioritize findings, build attack chains, and generate a reasoning summary.
        Must return structured output according to ReasoningResultSchema.
        """
        pass

    @abstractmethod
    async def plan_next_action(self, state: Dict[str, Any]) -> "NextActionSchema":
        """
        Determine the next iterative action based on current assessment state.
        Must return structured output according to NextActionSchema.
        """
        pass

    @abstractmethod
    async def evaluate_observation(self, action: Dict[str, Any], result: Dict[str, Any], state: Dict[str, Any]) -> "ObservationResultSchema":
        """
        Evaluate the result of a ToolRequest and return updated finding state and new surface area.
        Must return structured output according to ObservationResultSchema.
        """
        pass
