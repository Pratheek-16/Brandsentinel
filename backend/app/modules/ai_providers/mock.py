from .base import AIProvider

from ..deterministic.checks import run_deterministic_checks

class MockProvider(AIProvider):
    def generate_json(self, prompt: str, schema: dict, purpose: str) -> dict:
        """Run deterministic checks on the prompt and return findings.
        The schema argument is ignored because we always produce the
        exact structure required by the system.
        """
        # `prompt` is the raw text body of the content version.
        findings = run_deterministic_checks(prompt)
        # Ensure each finding matches the schema of the required output.
        # The schema expects a top‑level key "findings" with a list of objects.
        return {"findings": findings}

    def embed(self, texts):
        # Return zero vectors – deterministic placeholder for embedding.
        return [[0.0] * 768 for _ in texts]
