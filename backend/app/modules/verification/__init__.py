"""Verification utilities for BrandSentinel.
Ensures each finding matches the expected schema and drops invalid ones.
Simplified for demo: checks required fields, confidence range, and that the span text appears in the original content.
"""

from typing import List, Dict

def verify_findings(findings: List[Dict], original_text: str) -> List[Dict]:
    """Validate a list of finding dicts.
    - Required keys: category, severity, confidence, span, evidence, reason, suggestion, claim_status.
    - confidence must be a float between 0 and 1.
    - span.start/end must locate span.text inside original_text.
    - Deduplicate overlapping findings: keep the one with higher severity (blocker>major>minor>info).
    Returns a cleaned list.
    """
    severity_rank = {"blocker": 4, "major": 3, "minor": 2, "info": 1}
    cleaned = []
    for f in findings:
        # basic schema validation
        if not all(k in f for k in ("category", "severity", "confidence", "span", "evidence", "reason", "suggestion", "claim_status")):
            continue
        # confidence numeric
        try:
            conf = float(f["confidence"])
        except Exception:
            continue
        if not (0.0 <= conf <= 1.0):
            continue
        span = f["span"]
        if not all(k in span for k in ("start", "end", "text")):
            continue
        # verify span.text occurs at the given offsets (simple check)
        start, end, txt = span["start"], span["end"], span["text"]
        if original_text[start:end] != txt:
            continue
        # deduplication later
        cleaned.append(f)
    # deduplicate overlapping spans keeping highest severity
    result = []
    for f in cleaned:
        overlapping = False
        for r in result:
            s1, e1 = f["span"]["start"], f["span"]["end"]
            s2, e2 = r["span"]["start"], r["span"]["end"]
            if not (e1 <= s2 or e2 <= s1):  # overlap
                # keep higher severity
                if severity_rank[f["severity"]] > severity_rank[r["severity"]]:
                    result.remove(r)
                    result.append(f)
                overlapping = True
                break
        if not overlapping:
            result.append(f)
    return result
