# backend/app/agents/base.py
"""Base Agent Framework — common contract, lifecycle, and result abstractions for ARES agents."""

import logging
import time
from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentResult(BaseModel):
    """Standardized result returned by an agent execution."""

    agent_name: str
    role: str
    status: AgentState
    payload: Any = None
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    source_mode: str = "simulated"


class AgentException(Exception):
    """Custom exception raised when an agent encounters an unrecoverable failure."""

    def __init__(self, agent_name: str, operation: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"[{agent_name}] {operation} failed: {message}")
        self.agent_name = agent_name
        self.operation = operation
        self.message = message
        self.original_error = original_error


class BaseAgent:
    """Base class for all specialized ARES agents."""

    NAME: str = "BaseAgent"
    ROLE: str = "General Agent"
    DESCRIPTION: str = "Base agent abstraction for the ARES framework."

    def __init__(self, name: Optional[str] = None, role: Optional[str] = None, description: Optional[str] = None):
        self.name = name or self.NAME
        self.role = role or self.ROLE
        self.description = description or self.DESCRIPTION
        self.state: AgentState = AgentState.IDLE

    def set_state(self, state: AgentState):
        """Transition agent to a new lifecycle state."""
        logger.debug(f"Agent {self.name} state transition: {self.state} -> {state}")
        self.state = state

    async def run(self, action_name: str, func, *args, **kwargs) -> AgentResult:
        """
        Execute an agent action wrapped in lifecycle management, timing, and error handling.
        """
        self.set_state(AgentState.READY)
        start_time = time.perf_counter()
        self.set_state(AgentState.RUNNING)
        logger.info(f"[{self.name}] Starting operation '{action_name}'")

        try:
            result_payload = await func(*args, **kwargs)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.set_state(AgentState.COMPLETED)
            logger.info(f"[{self.name}] Completed operation '{action_name}' in {duration_ms}ms")

            return AgentResult(
                agent_name=self.name,
                role=self.role,
                status=AgentState.COMPLETED,
                payload=result_payload,
                execution_time_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.set_state(AgentState.FAILED)
            safe_msg = str(e)
            logger.error(f"[{self.name}] Operation '{action_name}' failed after {duration_ms}ms: {safe_msg}")

            raise AgentException(
                agent_name=self.name,
                operation=action_name,
                message=safe_msg,
                original_error=e,
            ) from e
