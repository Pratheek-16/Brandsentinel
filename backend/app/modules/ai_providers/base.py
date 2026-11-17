"""Base AI provider interface.
All providers must implement `generate_json` and `embed`.
"""

from typing import List, Any, Dict

class AIProvider:
    def generate_json(self, prompt: str, schema: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Generate a JSON response constrained by `schema`.
        Returns a dict matching the schema.
        """
        raise NotImplementedError

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors for the given texts."""
        raise NotImplementedError
