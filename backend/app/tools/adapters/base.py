from abc import ABC, abstractmethod
from app.schemas.tools import ToolRequest, ToolResult

class ToolAdapter(ABC):
    """
    Abstract base class for all tool adapters.
    Ensures a consistent interface (ToolRequest -> ToolResult)
    and prevents direct shell execution exposure.
    """

    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        """Execute the requested tool capability and return a normalized result."""
        pass
