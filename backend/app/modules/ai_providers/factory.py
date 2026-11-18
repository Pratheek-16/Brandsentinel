"""AI provider factory – selects provider based on environment variables.
If GEMINI_API_KEY is empty, returns deterministic MockProvider with 'AI provider: mock' ledger.
If GEMINI_API_KEY is present, initializes and returns GeminiProvider.
"""

from .mock import MockProvider

def get_provider():
    from ...core.config import settings
    if settings.gemini_api_key and settings.gemini_api_key.strip():
        try:
            from .gemini import GeminiProvider
            return GeminiProvider(api_key=settings.gemini_api_key.strip(), model_name=settings.llm_model)
        except Exception:
            return MockProvider()
    return MockProvider()
