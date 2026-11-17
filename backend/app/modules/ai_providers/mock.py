from .base import AIProvider

class MockProvider(AIProvider):
    def generate_json(self, prompt: str, schema: dict, purpose: str) -> dict:
        # Very simple deterministic mock: return empty findings list
        return {"findings": []}

    def embed(self, texts):
        # Return zero vectors
        return [[0.0] * 768 for _ in texts]
