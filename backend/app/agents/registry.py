# backend/app/agents/registry.py
"""Agent Registry for managing and inspecting ARES specialized agents."""

import logging
from typing import Dict, Type, List, Optional
from app.agents.base import BaseAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.recon_agent import ReconAgent
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.llm_reasoner import LLMReasoner
from app.agents.validation_agent import ValidationAgent
from app.schemas.schemas import AgentInfo

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry providing clean lookup and instantiation of specialized agents."""

    _agents: Dict[str, Type[BaseAgent]] = {
        PolicyAgent.NAME: PolicyAgent,
        ReconAgent.NAME: ReconAgent,
        AnalyzerAgent.NAME: AnalyzerAgent,
        LLMReasoner.NAME: LLMReasoner,
        ValidationAgent.NAME: ValidationAgent,
    }

    @classmethod
    def register(cls, agent_cls: Type[BaseAgent]):
        """Register a new agent class."""
        cls._agents[agent_cls.NAME] = agent_cls
        logger.info(f"Registered agent class: {agent_cls.NAME}")

    @classmethod
    def get_agent_class(cls, name: str) -> Optional[Type[BaseAgent]]:
        """Get an agent class by name."""
        return cls._agents.get(name)

    @classmethod
    def create_agent(cls, name: str) -> Optional[BaseAgent]:
        """Instantiate an agent by name."""
        agent_cls = cls.get_agent_class(name)
        if agent_cls:
            return agent_cls()
        return None

    @classmethod
    def list_agents(cls) -> List[BaseAgent]:
        """Instantiate and list all registered agents."""
        return [cls_type() for cls_type in cls._agents.values()]

    @classmethod
    def list_agent_info(cls) -> List[AgentInfo]:
        """List metadata for all registered agents."""
        result = []
        for name, cls_type in cls._agents.items():
            result.append(
                AgentInfo(
                    name=cls_type.NAME,
                    role=cls_type.ROLE,
                    description=cls_type.DESCRIPTION,
                    status="ready",
                )
            )
        return result
