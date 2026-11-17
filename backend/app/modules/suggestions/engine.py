"""Improvement I-1: Intent-Preserving Suggestion Engine with Self-Verification.
Generates candidate fixes for detected findings and verifies each by splicing it into
the text and re-running the verification pipeline to ensure:
1. The original finding is resolved.
2. No new findings of severity >= minor are introduced.
"""

from typing import List, Dict, Any, Optional, Tuple
from ..deterministic.checks import run_deterministic_checks
from ..verification import verify_findings

# Common brand term approved replacements and qualify patterns
REPLACEMENTS = {
    "guaranteed": "designed to provide reliable",
    "100% satisfaction guaranteed": "high satisfaction with dedicated support",
    "free forever": "transparent standard pricing",
    "$0 forever": "free starter tier available",
    "cheapest": "cost-effective",
    "best": "premier",
    "#1": "industry-leading",
    "cure": "support wellness and alleviate symptoms of",
}

def generate_candidate_suggestions(finding: Dict[str, Any], original_text: str) -> List[str]:
    """Generate 1-3 candidate replacements for the finding span."""
    span_text = finding["span"]["text"]
    candidates = []

    # 1. Direct dictionary match
    span_lower = span_text.lower()
    for trigger, repl in REPLACEMENTS.items():
        if trigger in span_lower:
            candidates.append(span_lower.replace(trigger, repl))

    # 2. Qualified phrasing
    if not candidates:
        if finding["category"] == "claim":
            candidates.append(f"{span_text}*")
            candidates.append(f"designed to help {span_text.lower()}")
        elif finding["category"] == "terminology":
            candidates.append(span_text.title())
        elif finding["category"] == "tone":
            candidates.append(f"courteously, {span_text.lower()}")
        else:
            candidates.append(f"[approved: {span_text}]")

    # Add general fallback if only 1
    if len(candidates) < 2:
        candidates.append(f"verified {span_text}")

    return candidates[:3]

def verify_suggestion(
    original_text: str,
    finding: Dict[str, Any],
    candidate_replacement: str,
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Splice replacement into text, re-run checks, verify that original finding is eliminated
    and no new findings of severity >= minor are introduced.
    """
    span_start = finding["span"]["start"]
    span_end = finding["span"]["end"]

    spliced_text = original_text[:span_start] + candidate_replacement + original_text[span_end:]

    # Re-run deterministic checks
    raw_new_findings = run_deterministic_checks(spliced_text)
    new_findings = verify_findings(raw_new_findings, spliced_text)

    # Check 1: Is original finding still present?
    orig_text = finding["span"]["text"]
    still_present = any(f["span"]["text"] == orig_text for f in new_findings)
    if still_present:
        return False, "Candidate does not eliminate the original brand violation.", new_findings

    # Check 2: Are new blocker/major findings created?
    severity_rank = {"blocker": 4, "major": 3, "minor": 2, "info": 1}
    introduced_severe = [f for f in new_findings if severity_rank.get(f["severity"], 1) >= 2]
    if introduced_severe:
        return False, f"Candidate introduces {len(introduced_severe)} new violations.", new_findings

    return True, "Verified: Resolves violation without introducing regressions.", new_findings

def get_verified_suggestions(
    original_text: str,
    finding: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Produce all verified suggestions for a finding."""
    candidates = generate_candidate_suggestions(finding, original_text)
    verified = []
    for cand in candidates:
        is_valid, reason, _ = verify_suggestion(original_text, finding, cand)
        if is_valid:
            verified.append({
                "replacement_text": cand,
                "verified": True,
                "verification_reason": reason,
            })
    return verified
