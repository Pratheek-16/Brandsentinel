"""Redaction utilities for BrandSentinel.
Detects PII (emails, phone numbers, credit card numbers, SSNs) and secrets (API keys, bearer tokens)
and replaces them with intent-preserving placeholders before sending content to AI providers.
Returns the redacted text, placeholder map, and category counts.
"""

import re
from typing import Tuple, Dict, Any

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
    if not text:
        return "", {}, {"email": 0, "phone": 0, "ssn": 0, "credit_card": 0, "secret": 0, "total": 0}

    placeholders: Dict[str, str] = {}
    counts: Dict[str, int] = {"email": 0, "phone": 0, "ssn": 0, "credit_card": 0, "secret": 0, "total": 0}

    def replace_secret(match):
        counts["secret"] += 1
        placeholder = f"<SECRET_{counts['secret']}>"
        placeholders[placeholder] = match.group(0)
        return placeholder

    def replace_cc(match):
        counts["credit_card"] += 1
        placeholder = f"<CREDIT_CARD_{counts['credit_card']}>"
        placeholders[placeholder] = match.group(0)
        return placeholder

    def replace_ssn(match):
        counts["ssn"] += 1
        placeholder = f"<SSN_{counts['ssn']}>"
        placeholders[placeholder] = match.group(0)
        return placeholder

    def replace_email(match):
        counts["email"] += 1
        placeholder = f"<EMAIL_{counts['email']}>"
        placeholders[placeholder] = match.group(0)
        return placeholder

    def replace_phone(match):
        counts["phone"] += 1
        placeholder = f"<PHONE_{counts['phone']}>"
        placeholders[placeholder] = match.group(0)
        return placeholder

    redacted = API_KEY_REGEX.sub(replace_secret, text)
    redacted = CREDIT_CARD_REGEX.sub(replace_cc, redacted)
    redacted = SSN_REGEX.sub(replace_ssn, redacted)
    redacted = EMAIL_REGEX.sub(replace_email, redacted)
    redacted = PHONE_REGEX.sub(replace_phone, redacted)

    counts["total"] = sum(v for k, v in counts.items() if k != "total")
    return redacted, placeholders, counts

def restore_text(text: str, placeholders: Dict[str, str]) -> str:
    """Restores original text from placeholders."""
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text
