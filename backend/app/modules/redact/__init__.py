"""Redaction utilities for BrandSentinel.
Detects PII (emails, phone numbers, credit card numbers, SSNs) and secrets (API keys, bearer tokens)
and replaces them with intent-preserving placeholders before sending content to AI providers.
Provides safe bidirectional character offset mapping between original and redacted text.
"""

import re
from typing import Tuple, Dict, Any, List

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
API_KEY_REGEX = re.compile(r"\b(?:AIza[0-9A-Za-z\\-_]{35}|AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|sk-[a-zA-Z0-9]{32,}|Bearer\s+[a-zA-Z0-9_\-\.]{20,})\b")

def redact_text(text: str) -> Tuple[str, Dict[str, str], Dict[str, int]]:
    """Redact sensitive PII and secrets in text.
    Returns:
      (redacted_text, placeholder_map, counts)
    """
    redacted, placeholders, counts, _ = redact_text_with_offsets(text)
    return redacted, placeholders, counts

def redact_text_with_offsets(text: str) -> Tuple[str, Dict[str, str], Dict[str, int], List[Dict[str, Any]]]:
    """Redacts sensitive PII and returns the replacement offset records for exact span mapping.
    Records format: [{"orig_start": ..., "orig_end": ..., "red_start": ..., "red_end": ..., "ph": ..., "val": ...}]
    """
    if not text:
        return "", {}, {"email": 0, "phone": 0, "ssn": 0, "credit_card": 0, "secret": 0, "total": 0}, []

    # Find all matches with their original spans
    matches = []
    for m in API_KEY_REGEX.finditer(text):
        matches.append((m.start(), m.end(), "secret", m.group(0)))
    for m in CREDIT_CARD_REGEX.finditer(text):
        matches.append((m.start(), m.end(), "credit_card", m.group(0)))
    for m in SSN_REGEX.finditer(text):
        matches.append((m.start(), m.end(), "ssn", m.group(0)))
    for m in EMAIL_REGEX.finditer(text):
        matches.append((m.start(), m.end(), "email", m.group(0)))
    for m in PHONE_REGEX.finditer(text):
        matches.append((m.start(), m.end(), "phone", m.group(0)))

    # Sort matches by start ascending, remove overlaps
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    non_overlapping = []
    last_end = 0
    for m in matches:
        if m[0] >= last_end:
            non_overlapping.append(m)
            last_end = m[1]

    placeholders: Dict[str, str] = {}
    counts: Dict[str, int] = {"email": 0, "phone": 0, "ssn": 0, "credit_card": 0, "secret": 0, "total": 0}
    offset_records: List[Dict[str, Any]] = []

    redacted_parts = []
    curr_orig_pos = 0
    curr_red_pos = 0

    for m_start, m_end, m_type, m_val in non_overlapping:
        # Append unchanged text preceding the match
        prefix = text[curr_orig_pos:m_start]
        redacted_parts.append(prefix)
        curr_red_pos += len(prefix)

        counts[m_type] += 1
        placeholder = f"<{m_type.upper()}_{counts[m_type]}>"
        placeholders[placeholder] = m_val

        ph_start = curr_red_pos
        ph_end = ph_start + len(placeholder)

        offset_records.append({
            "orig_start": m_start,
            "orig_end": m_end,
            "red_start": ph_start,
            "red_end": ph_end,
            "placeholder": placeholder,
            "original_val": m_val,
        })

        redacted_parts.append(placeholder)
        curr_red_pos += len(placeholder)
        curr_orig_pos = m_end

    # Append remaining text
    suffix = text[curr_orig_pos:]
    redacted_parts.append(suffix)
    redacted_text = "".join(redacted_parts)

    counts["total"] = sum(v for k, v in counts.items() if k != "total")
    return redacted_text, placeholders, counts, offset_records

def map_redacted_span_to_original(
    red_start: int,
    red_end: int,
    offset_records: List[Dict[str, Any]],
    original_text_len: int,
) -> Tuple[int, int]:
    """Maps (red_start, red_end) back to (orig_start, orig_end) in original unredacted text."""
    if not offset_records:
        return red_start, red_end

    def map_pos(pos: int) -> int:
        delta = 0
        for rec in offset_records:
            if pos < rec["red_start"]:
                break
            elif pos <= rec["red_end"]:
                # Position falls inside the placeholder: map to start of original entity
                return rec["orig_start"]
            else:
                # Position is after this replacement: adjust by length difference
                diff = (rec["red_end"] - rec["red_start"]) - (rec["orig_end"] - rec["orig_start"])
                delta += diff
        return max(0, min(original_text_len, pos - delta))

    orig_start = map_pos(red_start)
    orig_end = map_pos(red_end)
    if orig_end < orig_start:
        orig_end = orig_start
    return orig_start, orig_end

def restore_text(text: str, placeholders: Dict[str, str]) -> str:
    """Restores original text from placeholders."""
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text
