import re
from typing import List, Dict

# Simple deterministic rule definitions
BANNED_TERMS = {"foobar", "lorem", "bad"}
GUARANTEE_PHRASES = {"guaranteed", "100% safe", "cure"}

def find_spans(text: str, pattern: re.Pattern) -> List[Dict[str, any]]:
    """Return a list of spans (start, end, text) where pattern matches."""
    spans = []
    for m in pattern.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "text": m.group()})
    return spans

def run_deterministic_checks(text: str) -> List[Dict[str, any]]:
    """Run a set of deterministic, rule‑based checks on the given text.
    Returns a list of finding dictionaries matching the required schema.
    """
    findings = []
    lowered = text.lower()
    # 1. Banned term check (terminology)
    for term in BANNED_TERMS:
        if term in lowered:
            for span in find_spans(text, re.compile(re.escape(term), re.IGNORECASE)):
                findings.append({
                    "category": "terminology",
                    "severity": "major",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {"type": "term", "id": term.upper(), "quote": term},
                    "reason": f"Banned term '{term}' used.",
                    "suggestion": {"text": f"Replace '{term}' with an approved alternative."},
                    "claim_status": "n/a",
                })
    # 2. Guarantee phrases (claim)
    for phrase in GUARANTEE_PHRASES:
        if phrase.lower() in lowered:
            for span in find_spans(text, re.compile(re.escape(phrase), re.IGNORECASE)):
                findings.append({
                    "category": "claim",
                    "severity": "blocker",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {"type": "rule", "id": "R-CLAIM-GUARANTEE", "quote": phrase},
                    "reason": f"Prohibited guarantee phrase '{phrase}'.",
                    "suggestion": {"text": f"Remove or qualify the guarantee statement."},
                    "claim_status": "unsupported",
                })
    # 3. Simple numeric claim mismatch (example): look for "$0" price claim
    price_pattern = re.compile(r"\$\s*0\b")
    for span in find_spans(text, price_pattern):
        findings.append({
            "category": "claim",
            "severity": "minor",
            "confidence": 0.9,
            "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
            "evidence": {"type": "fact", "id": "F-PRICE-ZERO", "quote": "$0"},
            "reason": "Price claim of $0 is unrealistic.",
            "suggestion": {"text": "Provide a realistic price or remove the claim."},
            "claim_status": "contradicted",
        })
    return findings
