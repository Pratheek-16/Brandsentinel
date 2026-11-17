"""Gemini AI Provider implementation for BrandSentinel.
Connects to Google Gemini API via google-generativeai.
Activated ONLY when GEMINI_API_KEY environment variable is configured.
"""

import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name if model_name and model_name != "mock" else "gemini-1.5-flash"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate_json(self, prompt: str, schema: dict, purpose: str) -> dict:
        """Call Gemini model with structured JSON enforcement."""
        system_instruction = (
            f"You are BrandSentinel, an expert brand-governance auditor for purpose: '{purpose}'. "
            f"Review the submitted content text strictly against brand guidelines and evidence. "
            f"Return a valid JSON object matching the required schema with a list of findings."
        )
        full_prompt = (
            f"{system_instruction}\n\n"
            f"Content to review:\n{prompt}\n\n"
            f"Expected schema format:\n{json.dumps(schema)}"
        )
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            data = json.loads(response.text)
            return data if isinstance(data, dict) else {"findings": []}
        except Exception as e:
            # Fallback gracefully if rate limit or network issue occurs
            return {"findings": [], "error": str(e)}

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Compute text embeddings using Gemini embedding model."""
        embeddings: List[List[float]] = []
        for text in texts:
            try:
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document",
                )
                embeddings.append(res["embedding"])
            except Exception:
                # 768-dim fallback
                embeddings.append([0.0] * 768)
        return embeddings
