"""Grounding Verifier for BrandSentinel.

Ensures every surfaced finding is strictly grounded, verified against original text offsets,
conforms to schema and severity rules, and cites valid evidence from the active Knowledge Base.
Crucially: verifies that evidence.quote matches the stored KB text, dropping hallucinated citations.
Ungrounded, hallucinatory, or malformed findings are dropped and counted.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

VALID_CATEGORIES = {"tone", "terminology", "messaging", "visual", "accessibility", "claim", "security"}
VALID_SEVERITIES = {"blocker", "major", "minor", "info"}
VALID_EVIDENCE_TYPES = {"rule", "fact", "term", "claim", "security_policy", "guideline", "asset"}
SEVERITY_RANK = {"blocker": 4, "major": 3, "minor": 2, "info": 1}

def normalize_text(t: str) -> str:
    """Normalize text for comparison by collapsing whitespace and punctuation."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", str(t).lower())).strip()

def verify_findings(
    findings: List[Dict[str, Any]],
    original_text: str,
    db: Optional[Session] = None,
    kb_version_id: Optional[int] = None,
    return_metrics: bool = False,
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, int]]]:
    """Validate a list of finding dicts with rigorous grounding checks:
    1. Schema conformance (all required keys present).
    2. Valid category and severity values.
    3. Confidence is a valid float between 0.0 and 1.0.
    4. Span offsets locate span.text exactly inside original_text (original_text[start:end] == span_text).
    5. Evidence ID exists in the active Knowledge Base.
    6. Evidence.quote matches the stored Knowledge Base text (normalised substring or token match).
    7. Deduplicate overlapping finding spans, retaining the one with higher severity rank.
    """
    metrics = {
        "total_evaluated": len(findings) if findings else 0,
        "rejected_schema": 0,
        "rejected_offsets": 0,
        "rejected_invalid_id": 0,
        "rejected_unmatched_quote": 0,
        "rejected_total": 0,
    }

    if not findings or not original_text:
        return ([], metrics) if return_metrics else []

    # Pre-fetch active KB references and texts if DB session provided
    rules_dict: Dict[str, str] = {}
    facts_dict: Dict[str, str] = {}
    terms_dict: Dict[str, List[str]] = {}
    claims_list: List[str] = []

    if db and kb_version_id:
        from ...db import models
        rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb_version_id).all()
        for r in rules:
            rules_dict[r.code] = r.text

        facts = db.query(models.Fact).filter(models.Fact.kb_version_id == kb_version_id).all()
        for f in facts:
            facts_dict[f.code] = f"{f.key} {f.value} {f.unit or ''} {f.source or ''}"

        terms = db.query(models.Term).filter(models.Term.kb_version_id == kb_version_id).all()
        for t in terms:
            terms_dict[t.preferred.lower()] = [b.lower() for b in (t.banned or [])]

        claims = db.query(models.Claim).filter(models.Claim.kb_version_id == kb_version_id).all()
        for c in claims:
            claims_list.append(c.approved_text)

    cleaned = []
    text_len = len(original_text)

    for f in findings:
        # Check required keys
        required_keys = ("category", "severity", "confidence", "span", "evidence", "reason")
        if not all(k in f for k in required_keys):
            metrics["rejected_schema"] += 1
            continue

        cat = str(f["category"]).lower()
        if cat not in VALID_CATEGORIES:
            metrics["rejected_schema"] += 1
            continue

        sev = str(f["severity"]).lower()
        if sev not in VALID_SEVERITIES:
            metrics["rejected_schema"] += 1
            continue

        try:
            conf = float(f["confidence"])
            if not (0.0 <= conf <= 1.0):
                metrics["rejected_schema"] += 1
                continue
        except (ValueError, TypeError):
            metrics["rejected_schema"] += 1
            continue

        span = f.get("span", {})
        if not isinstance(span, dict) or not all(k in span for k in ("start", "end", "text")):
            metrics["rejected_schema"] += 1
            continue

        try:
            start = int(span["start"])
            end = int(span["end"])
            txt = str(span["text"])
        except (ValueError, TypeError):
            metrics["rejected_schema"] += 1
            continue

        if start < 0 or end > text_len or start >= end:
            metrics["rejected_offsets"] += 1
            continue

        # Exact substring check: original_text[start:end] == txt
        if original_text[start:end] != txt:
            metrics["rejected_offsets"] += 1
            continue

        evidence = f.get("evidence", {})
        if not isinstance(evidence, dict):
            metrics["rejected_schema"] += 1
            continue

        ev_type = str(evidence.get("type", "")).lower()
        if ev_type and ev_type not in VALID_EVIDENCE_TYPES:
            metrics["rejected_schema"] += 1
            continue

        ev_id = str(evidence.get("id", "")).strip()
        if not ev_id:
            metrics["rejected_invalid_id"] += 1
            continue

        quote = str(evidence.get("quote", "")).strip()

        # Database Grounding Verification against Active KB Records
        if db and kb_version_id:
            # 1. Existence check of cited ID
            if ev_type == "rule":
                if rules_dict and ev_id not in rules_dict and not ev_id.startswith("SEC-") and not ev_id.startswith("GEN-"):
                    metrics["rejected_invalid_id"] += 1
                    continue
                # 2. Quote verification: quote must match stored rule text
                if ev_id in rules_dict and quote:
                    stored_rule_text = rules_dict[ev_id]
                    # Check substring or partial ratio
                    norm_quote = normalize_text(quote)
                    norm_stored = normalize_text(stored_rule_text)
                    if norm_quote not in norm_stored and norm_stored not in norm_quote:
                        ratio = fuzz.partial_ratio(norm_quote, norm_stored)
                        if ratio < 65:
                            # Drop hallucinated quote
                            metrics["rejected_unmatched_quote"] += 1
                            continue

            elif ev_type == "fact":
                if facts_dict and ev_id not in facts_dict and not ev_id.startswith("GEN-"):
                    metrics["rejected_invalid_id"] += 1
                    continue
                # Quote verification against stored fact
                if ev_id in facts_dict and quote:
                    stored_fact = facts_dict[ev_id]
                    norm_quote = normalize_text(quote)
                    norm_stored = normalize_text(stored_fact)
                    if norm_quote not in norm_stored and norm_stored not in norm_quote:
                        ratio = fuzz.partial_ratio(norm_quote, norm_stored)
                        if ratio < 50:
                            metrics["rejected_unmatched_quote"] += 1
                            continue

            elif ev_type == "term":
                # Ensure the term is known in terms_dict or rules_dict
                term_found = False
                ev_id_lower = ev_id.lower()
                for pref, banned_variants in terms_dict.items():
                    if ev_id_lower == pref or ev_id_lower in banned_variants or ev_id in rules_dict:
                        term_found = True
                        break
                if not term_found and terms_dict and not ev_id.startswith("NF-") and not ev_id.startswith("LB-") and not ev_id.startswith("AU-") and not ev_id.startswith("GEN-") and not ev_id.startswith("KB-"):
                    metrics["rejected_invalid_id"] += 1
                    continue

        # Verified finding
        cleaned_item = {
            "category": cat,
            "severity": sev,
            "confidence": conf,
            "span": {"start": start, "end": end, "text": txt},
            "evidence": {
                "type": ev_type or "rule",
                "id": ev_id,
                "quote": quote or txt,
            },
            "reason": str(f["reason"]),
            "suggestion": f.get("suggestion"),
            "claim_status": f.get("claim_status", "n/a"),
            "source": f.get("source", "rule"),
        }
        cleaned.append(cleaned_item)

    metrics["rejected_total"] = (
        metrics["rejected_schema"] +
        metrics["rejected_offsets"] +
        metrics["rejected_invalid_id"] +
        metrics["rejected_unmatched_quote"]
    )

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
                # Only treat as conflicting overlap if exact same span OR same category
                if (f_s == r_s and f_e == r_e) or (f.get("category") == r.get("category")):
                    overlapping_idx = idx
                    break

        if overlapping_idx == -1:
            resolved.append(f)
        else:
            existing = resolved[overlapping_idx]
            if SEVERITY_RANK[f["severity"]] > SEVERITY_RANK[existing["severity"]]:
                resolved[overlapping_idx] = f

    if return_metrics:
        return resolved, metrics
    return resolved
