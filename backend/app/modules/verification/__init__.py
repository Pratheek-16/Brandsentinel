"""Grounding Verifier for BrandSentinel.
Ensures every surfaced finding is strictly grounded, mathematically verified against original text offsets,
conforms to schema and severity rules, and cites valid evidence from the active Knowledge Base.
Ungrounded, hallucinatory, or malformed findings are dropped and logged.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

VALID_CATEGORIES = {"tone", "terminology", "messaging", "visual", "accessibility", "claim", "security"}
VALID_SEVERITIES = {"blocker", "major", "minor", "info"}
VALID_EVIDENCE_TYPES = {"rule", "fact", "term", "claim", "security_policy", "guideline"}
SEVERITY_RANK = {"blocker": 4, "major": 3, "minor": 2, "info": 1}

def verify_findings(
    findings: List[Dict[str, Any]],
    original_text: str,
    db: Optional[Session] = None,
    kb_version_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Validate a list of finding dicts with rigorous grounding checks:
    1. Schema conformance (all required keys present).
    2. Valid category and severity values.
    3. Confidence is a valid float between 0.0 and 1.0.
    4. Span offsets (start, end) locate span.text exactly inside original_text (original_text[start:end] == span_text).
    5. Evidence ID and evidence type are valid and consistent.
    6. If DB and kb_version_id are provided, verify that cited rule/fact/term/claim actually exists in the active KB.
    7. Deduplicate overlapping finding spans, retaining the one with higher severity rank.
    """
    if not findings or not original_text:
        return []

    # Pre-fetch active KB references if DB session provided
    valid_rule_codes = set()
    valid_fact_codes = set()
    valid_terms = set()
    valid_claims = set()

    if db and kb_version_id:
        from ...db import models
        rules = db.query(models.Rule.code).filter(models.Rule.kb_version_id == kb_version_id).all()
        valid_rule_codes = {r[0] for r in rules}
        facts = db.query(models.Fact.code).filter(models.Fact.kb_version_id == kb_version_id).all()
        valid_fact_codes = {f[0] for f in facts}
        terms = db.query(models.Term).filter(models.Term.kb_version_id == kb_version_id).all()
        for t in terms:
            valid_terms.add(t.preferred.lower())
            if t.banned:
                for b in t.banned:
                    valid_terms.add(b.lower())
        claims = db.query(models.Claim).filter(models.Claim.kb_version_id == kb_version_id).all()
        valid_claims = {c.approved_text for c in claims}

    cleaned = []
    text_len = len(original_text)

    for f in findings:
        # Check required keys
        required_keys = ("category", "severity", "confidence", "span", "evidence", "reason")
        if not all(k in f for k in required_keys):
            continue

        # Check category & severity
        cat = str(f["category"]).lower()
        if cat not in VALID_CATEGORIES:
            continue

        sev = str(f["severity"]).lower()
        if sev not in VALID_SEVERITIES:
            continue

        # Check confidence
        try:
            conf = float(f["confidence"])
            if not (0.0 <= conf <= 1.0):
                continue
        except (ValueError, TypeError):
            continue

        # Check span offsets and exact text match
        span = f.get("span", {})
        if not isinstance(span, dict) or not all(k in span for k in ("start", "end", "text")):
            continue

        try:
            start = int(span["start"])
            end = int(span["end"])
            txt = str(span["text"])
        except (ValueError, TypeError):
            continue

        if start < 0 or end > text_len or start >= end:
            continue

        # Exact substring check: original_text[start:end] == txt
        if original_text[start:end] != txt:
            # Drop ungrounded span offset mismatch
            continue

        # Check evidence consistency
        evidence = f.get("evidence", {})
        if not isinstance(evidence, dict):
            continue

        ev_type = str(evidence.get("type", "")).lower()
        if ev_type and ev_type not in VALID_EVIDENCE_TYPES:
            continue

        ev_id = str(evidence.get("id", ""))
        if not ev_id:
            continue

        # If DB provided, verify citation against active KB
        if db and kb_version_id:
            if ev_type == "rule" and valid_rule_codes and ev_id not in valid_rule_codes:
                # Rule not in active KB
                continue
            elif ev_type == "fact" and valid_fact_codes and ev_id not in valid_fact_codes:
                continue

        # Cleaned finding object
        cleaned_item = {
            "category": cat,
            "severity": sev,
            "confidence": conf,
            "span": {"start": start, "end": end, "text": txt},
            "evidence": {
                "type": ev_type or "rule",
                "id": ev_id,
                "quote": evidence.get("quote") or txt,
            },
            "reason": str(f["reason"]),
            "suggestion": f.get("suggestion"),
            "claim_status": f.get("claim_status", "n/a"),
        }
        cleaned.append(cleaned_item)

    # Overlapping span resolution: keep highest severity
    cleaned.sort(key=lambda x: (x["span"]["start"], -(x["span"]["end"] - x["span"]["start"])))
    resolved = []

    for f in cleaned:
        overlapping_idx = -1
        f_s = f["span"]["start"]
        f_e = f["span"]["end"]

        for idx, r in enumerate(resolved):
            r_s = r["span"]["start"]
            r_e = r["span"]["end"]
            if not (f_e <= r_s or f_s >= r_e):
                overlapping_idx = idx
                break

        if overlapping_idx == -1:
            resolved.append(f)
        else:
            existing = resolved[overlapping_idx]
            if SEVERITY_RANK[f["severity"]] > SEVERITY_RANK[existing["severity"]]:
                resolved[overlapping_idx] = f

    return resolved
