from .provider import LLMProvider
from .mock_provider import MockProvider
from .omniroute_provider import OmniRouteProvider
from app.core.config import settings

def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER.lower() == "omniroute":
        return OmniRouteProvider()
    return MockProvider()
