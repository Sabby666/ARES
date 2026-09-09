import logging
from typing import Dict, Type
from app.tools.adapters.base import ToolAdapter
from app.tools.adapters.mock import MockReconAdapter, MockHttpAnalysisAdapter, MockValidationAdapter
from app.tools.adapters.hexstrike import HexStrikeAdapter
from app.schemas.policy import ActionCapability
from app.core.config import settings

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Maintains a mapping of allowed capabilities to their respective adapters."""

    def __init__(self):
        self._adapters: Dict[str, Type[ToolAdapter]] = {}
        
        if settings.TOOL_PROVIDER == "hexstrike":
            logger.info("ToolRegistry initialized in HEXSTRIKE mode.")
            self._adapters = {
                ActionCapability.RECON: HexStrikeAdapter,
                ActionCapability.VALIDATION: HexStrikeAdapter,
                ActionCapability.DISCOVERY: HexStrikeAdapter,
                ActionCapability.EXPLOITATION: HexStrikeAdapter,
                ActionCapability.BRUTE_FORCE: HexStrikeAdapter,
                ActionCapability.COMMAND_INJECTION: HexStrikeAdapter,
                ActionCapability.SQL_INJECTION: HexStrikeAdapter,
                ActionCapability.XSS: HexStrikeAdapter,
                ActionCapability.AUTHENTICATION_TEST: HexStrikeAdapter,
            }
        else:
            logger.info("ToolRegistry initialized in MOCK mode.")
            self._adapters = {
                ActionCapability.RECON: MockReconAdapter,
                ActionCapability.HTTP_ANALYSIS: MockHttpAnalysisAdapter,
                ActionCapability.VALIDATION: MockValidationAdapter,
                ActionCapability.DISCOVERY: MockReconAdapter,
                ActionCapability.VULNERABILITY_ANALYSIS: MockHttpAnalysisAdapter,
                ActionCapability.EXPLOITATION: MockValidationAdapter,
                ActionCapability.BRUTE_FORCE: MockValidationAdapter,
                ActionCapability.COMMAND_INJECTION: MockValidationAdapter,
                ActionCapability.SQL_INJECTION: MockValidationAdapter,
                ActionCapability.XSS: MockValidationAdapter,
                ActionCapability.AUTHENTICATION_TEST: MockValidationAdapter,
            }

    def get_adapter(self, capability: str) -> ToolAdapter:
        """Resolve a capability string to an adapter instance."""
        adapter_cls = self._adapters.get(capability)
        if not adapter_cls:
            raise ValueError(f"Capability '{capability}' is not registered.")
        return adapter_cls()
