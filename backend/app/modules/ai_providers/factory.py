"""AI provider factory – selects provider based on environment variables.
If GEMINI_API_KEY is empty, returns MockProvider; otherwise returns GeminiProvider (placeholder).
"""

import os
from .mock import MockProvider
# Placeholder for real Gemini provider – not implemented to avoid external calls

def get_provider():
    from ...core.config import settings
    if settings.gemini_api_key:
        # In a real implementation, you'd import and init GeminiProvider here.
        # For now we fallback to MockProvider to keep the app runnable offline.
        return MockProvider()
    return MockProvider()
