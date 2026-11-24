"""Claim Ledger implementation for BrandSentinel.

Tracks promotional and factual claims in content against the organisation's approved Claims library.
Evaluates every claim as:
- 'supported' (or 'approved'): matches an approved claim with valid dates and disclaimer present.
- 'missing_disclaimer': matches approved claim but required disclaimer text is missing.
- 'outdated' (or 'expired'): matches an approved claim whose valid_to date has passed.
- 'contradicted': directly contradicts or misrepresents an approved claim on file.
- 'unsupported': unverified or prohibited promotional claim without approved evidence.
"""

import re
import datetime
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from ...core.datetime_utils import utc_now

CLAIM_TRIGGERS = [
    re.compile(r"\b(\d+%\s+(?:faster|better|effective|satisfaction|uptime|reduction|increase|cheaper))\b", re.IGNORECASE),
    re.compile(r"\b(clinically\s+(?:proven|tested|validated))\b", re.IGNORECASE),
    re.compile(r"\b(guaranteed|100%\s+guarantee|risk-free\s+guarantee|guarantee\w*)\b", re.IGNORECASE),
    re.compile(r"\b(fastest|best|cheapest|#1|rated\s+#1|number\s+one)\b", re.IGNORECASE),
    re.compile(r"\b(cure[s]?|treat[s]?|prevent[s]?)\b", re.IGNORECASE),
    re.compile(r"\b(free\s+forever|\$0\s+forever|unlimited\s+for\s+free|zero\s+risk|no\s+chance\s+of\s+loss)\b", re.IGNORECASE),
]

def extract_candidate_claims(text: str) -> List[Dict[str, Any]]:
    claims = []
    seen_spans = set()
    for pattern in CLAIM_TRIGGERS:
        for m in pattern.finditer(text):
            span_key = (m.start(), m.end())
            if span_key not in seen_spans:
                seen_spans.add(span_key)
                claims.append({
                    "start": m.start(),
                    "end": m.end(),
                    "claim_text": m.group(0),
                })
    return claims

def evaluate_claims(
    content_text: str,
    approved_claims: List[Any],
) -> List[Dict[str, Any]]:
    extracted = extract_candidate_claims(content_text)
    ledger = []
    now = utc_now()

    for item in extracted:
        claim_str = item["claim_text"]
        best_match = None
        best_score = 0.0

        for ac in approved_claims:
            score = fuzz.partial_ratio(claim_str.lower(), ac.approved_text.lower())
            if score > best_score:
                best_score = score
                best_match = ac

        if best_match and best_score >= 70.0:
            # Check validity date
            if best_match.valid_to and best_match.valid_to < now:
                status = "outdated"
                reason = f"Approved claim expired on {best_match.valid_to.strftime('%Y-%m-%d')}."
            elif best_match.required_disclaimer and best_match.required_disclaimer.lower() not in content_text.lower():
                status = "missing_disclaimer"
                reason = f"Approved claim requires mandatory disclaimer: '{best_match.required_disclaimer}'."
            else:
                status = "supported"
                reason = "Matches approved claim in Knowledge Base."

            ledger.append({
                "claim_text": claim_str,
                "span_start": item["start"],
                "span_end": item["end"],
                "status": status,
                "legacy_status": "approved" if status == "supported" else ("expired" if status == "outdated" else status),
                "reason": reason,
                "evidence_ref": best_match.evidence_ref,
                "required_disclaimer": best_match.required_disclaimer,
                "approved_text": best_match.approved_text,
            })
        else:
            # Check if this is a contradicted claim (e.g., claiming 0% risk when products are risk-bearing)
            lower_claim = claim_str.lower()
            if any(term in lower_claim for term in ["zero risk", "no chance of loss", "100% cure"]):
                status = "contradicted"
                reason = "Contradicts mandatory brand regulatory standards: risk-free or unconditional claims are prohibited."
            else:
                status = "unsupported"
                reason = "Unsupported promotional claim without verified evidence in Brand Knowledge Base."

            ledger.append({
                "claim_text": claim_str,
                "span_start": item["start"],
                "span_end": item["end"],
                "status": status,
                "legacy_status": status,
                "reason": reason,
                "evidence_ref": None,
                "required_disclaimer": None,
                "approved_text": None,
            })

    return ledger
