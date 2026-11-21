"""MockLLM Test Double for Reliability and Verifier Verification (Priority 2).

Simulates varied LLM behaviors and failure modes for testing:
1. Hallucinated Rule IDs (rules not in Knowledge Base).
2. Fabricated Quotes (quotes not matching stored KB text).
3. Mismatched Span Offsets (character offsets not matching content text).
4. Prompt-injection obedience attempts.
5. Legitimate, perfectly grounded findings.
"""

from typing import List, Dict, Any, Optional
from .base import AIProvider

class MockLLM(AIProvider):
    def __init__(self, mode: str = "grounded"):
        """Modes:
        - 'grounded': Returns compliant, perfectly grounded findings.
        - 'hallucinate_id': Returns finding citing non-existent rule 'HALLUCINATED-RULE-999'.
        - 'wrong_quote': Returns real rule ID but completely fabricated quote.
        - 'offset_mismatch': Returns span where span.start/end does not match span.text.
        - 'malformed_json': Returns broken/invalid JSON structure.
        - 'rate_limit': Simulates 429 quota exhaustion.
        """
        self.mode = mode

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        purpose: str = "review",
        retrieved_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if self.mode == "rate_limit":
            return {"findings": [], "error": "AI unavailable: Gemini quota or rate limit exceeded", "ai_status": "rate_limited"}

        if self.mode == "malformed_json":
            return {"findings": [], "error": "AI response was not valid JSON", "ai_status": "invalid_json"}

        if self.mode == "hallucinate_id":
            # Finding cites non-existent rule
            return {
                "findings": [
                    {
                        "category": "tone",
                        "severity": "major",
                        "confidence": 0.95,
                        "span": {"start": 0, "end": 10, "text": prompt[:10] if len(prompt) >= 10 else prompt},
                        "evidence": {
                            "type": "rule",
                            "id": "HALLUCINATED-RULE-999",
                            "quote": "Invented rule that does not exist in any brand book"
                        },
                        "reason": "Hallucinated finding citing phantom rule ID.",
                        "suggestion": {"text": "Rewrite to follow phantom rule"},
                        "source": "ai",
                    }
                ]
            }

        if self.mode == "wrong_quote":
            # Finding cites a real rule code but fabricates the quote
            rule_id = "NF-TONE-01"
            if retrieved_evidence and len(retrieved_evidence) > 0:
                rule_id = retrieved_evidence[0].get("id", "NF-TONE-01")

            return {
                "findings": [
                    {
                        "category": "tone",
                        "severity": "major",
                        "confidence": 0.92,
                        "span": {"start": 0, "end": 10, "text": prompt[:10] if len(prompt) >= 10 else prompt},
                        "evidence": {
                            "type": "rule",
                            "id": rule_id,
                            "quote": "Completely invented quote about flying elephants and quantum lasers."
                        },
                        "reason": "Hallucinated quote attached to real rule code.",
                        "suggestion": {"text": "Rewrite with valid tone"},
                        "source": "ai",
                    }
                ]
            }

        if self.mode == "offset_mismatch":
            # Span offsets (0, 10) point to prompt[:10], but span.text is totally different
            return {
                "findings": [
                    {
                        "category": "tone",
                        "severity": "major",
                        "confidence": 0.90,
                        "span": {"start": 0, "end": 10, "text": "COMPLETELY_WRONG_SPAN_TEXT"},
                        "evidence": {
                            "type": "rule",
                            "id": "NF-TONE-01",
                            "quote": "Empowering, energetic, and encouraging"
                        },
                        "reason": "Span offset mismatch hallucination.",
                        "suggestion": {"text": "Fix offset mismatch"},
                        "source": "ai",
                    }
                ]
            }

        # Grounded mode
        rule_id = "NF-TONE-01"
        rule_text = "Empowering, energetic, and encouraging; never shaming, preachy, or punitive."
        if retrieved_evidence:
            for ev in retrieved_evidence:
                if ev.get("type") == "rule":
                    rule_id = ev.get("id")
                    rule_text = ev.get("text", rule_text)
                    break

        s_text = prompt[:15] if len(prompt) >= 15 else prompt
        return {
            "findings": [
                {
                    "category": "tone",
                    "severity": "major",
                    "confidence": 0.95,
                    "span": {"start": 0, "end": len(s_text), "text": s_text},
                    "evidence": {
                        "type": "rule",
                        "id": rule_id,
                        "quote": rule_text,
                    },
                    "reason": f"Grounded AI finding citing {rule_id}.",
                    "suggestion": {"text": "Celebrate and empower progress"},
                    "source": "ai",
                }
            ]
        }

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 768 for _ in texts]
