"""Rule atomisation engine for BrandSentinel.
Takes unstructured guideline documents (plain text, markdown, or lists) and breaks them
down into distinct, atomic, testable candidate brand rules with category, severity, and code.
The output is presented to the Brand Guardian for confirmation before insertion into the KB.
"""

import re
from typing import List, Dict, Any

CATEGORY_KEYWORDS = {
    "tone": ["tone", "voice", "empathetic", "friendly", "formal", "humorous", "respectful", "passive voice", "concise"],
    "terminology": ["term", "terminology", "nomenclature", "capitalization", "acronym", "spelling", "naming", "glossary"],
    "messaging": ["message", "positioning", "mission", "pillar", "value proposition", "boilerplate", "story"],
    "visual": ["logo", "palette", "color", "font", "typography", "spacing", "clearspace", "rgb", "hex", "asset"],
    "accessibility": ["accessibility", "contrast", "wcag", "alt text", "readability", "screen reader", "aria", "legible"],
    "claim": ["claim", "guarantee", "statistic", "percent", "study", "fda", "certified", "fastest", "cheapest", "uptime"],
}

SEVERITY_KEYWORDS = {
    "blocker": ["never", "strictly prohibited", "forbidden", "illegal", "must not", "critical", "mandatory", "zero tolerance"],
    "major": ["should not", "avoid", "strongly discouraged", "required", "do not", "prohibited"],
    "minor": ["prefer", "recommend", "consider", "better to", "generally"],
    "info": ["note", "guideline", "tip", "context", "optional"],
}

def detect_category(text: str) -> str:
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in text_lower:
                scores[cat] += 1
    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "tone"

def detect_severity(text: str) -> str:
    text_lower = text.lower()
    for sev in ["blocker", "major", "minor"]:
        for kw in SEVERITY_KEYWORDS[sev]:
            if kw in text_lower:
                return sev
    return "minor"

def atomise_guidelines(text: str) -> List[Dict[str, Any]]:
    """Parse text into atomic rule candidates.
    Splits on numbered lists, bullet points, headers, or distinct sentences.
    """
    candidates: List[Dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    rule_idx = 1
    current_block = []

    for line in lines:
        # Check if line looks like a header or list item
        is_bullet = re.match(r"^[-*•\d+\.]\s+", line)
        is_header = line.startswith("#")

        if (is_bullet or is_header) and current_block:
            item_text = " ".join(current_block)
            if len(item_text) > 10:
                cat = detect_category(item_text)
                sev = detect_severity(item_text)
                code = f"R-{cat[:4].upper()}-{rule_idx:03d}"
                candidates.append({
                    "code": code,
                    "category": cat,
                    "text": item_text,
                    "severity_default": sev,
                    "channels": ["all"],
                    "examples_good": [],
                    "examples_bad": [],
                    "status": "candidate",
                })
                rule_idx += 1
            current_block = []

        cleaned_line = re.sub(r"^[-*#•\d+\.]\s*", "", line).strip()
        if cleaned_line:
            current_block.append(cleaned_line)

    if current_block:
        item_text = " ".join(current_block)
        if len(item_text) > 10:
            cat = detect_category(item_text)
            sev = detect_severity(item_text)
            code = f"R-{cat[:4].upper()}-{rule_idx:03d}"
            candidates.append({
                "code": code,
                "category": cat,
                "text": item_text,
                "severity_default": sev,
                "channels": ["all"],
                "examples_good": [],
                "examples_bad": [],
                "status": "candidate",
            })

    return candidates
