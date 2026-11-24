"""Knowledge-Base-Driven Deterministic Engine for BrandSentinel.

Evaluates content text dynamically against the ACTIVE Knowledge Base version:
1. Terms: Banned variants, preferred terms, and casing rules.
2. Rules: Category (tone, messaging, accessibility, etc.), severity, channels, and bad/good examples.
3. Facts: Numeric and date assertions compared against approved facts (flags 'contradicted' and 'outdated').
4. Claims: Evaluated against the workspace claim register ('supported', 'missing_disclaimer', 'outdated', 'contradicted', 'unsupported').
5. Security: Prompt-injection and adversarial review-bypass checks.
"""

import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from ...db import models
from ...core.datetime_utils import utc_now
from .checks import INJECTION_PATTERNS


def find_spans(text: str, pattern: re.Pattern) -> List[Dict[str, Any]]:
    spans = []
    for m in pattern.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "text": m.group(0)})
    return spans


def extract_numbers_with_context(text: str) -> List[Dict[str, Any]]:
    """Extract numeric values, units, and surrounding sentence context from text."""
    # Matches patterns like: 14 days, 5 ATM, $4,999, 4.85%, 12.4%, 250,000, 20 lbs
    num_pattern = re.compile(
        r"(?:(?:\$|Rs\.?|₹|€|£)\s*)?(\b\d{1,3}(?:,\d{3})*(?:\.\d+)?|\b\d+(?:\.\d+)?)\s*([a-zA-Z%]+)?",
        re.IGNORECASE
    )
    results = []
    for m in num_pattern.finditer(text):
        val_str = m.group(1).replace(",", "")
        unit_str = (m.group(2) or "").lower()
        try:
            val_float = float(val_str)
        except ValueError:
            continue

        # Look at window of 60 chars before and after for entity keywords
        window_start = max(0, m.start() - 60)
        window_end = min(len(text), m.end() + 60)
        context = text[window_start:window_end].lower()

        results.append({
            "start": m.start(),
            "end": m.end(),
            "text": m.group(0),
            "val": val_float,
            "raw_val": val_str,
            "unit": unit_str,
            "context": context,
        })
    return results


def run_kb_checks(
    text: str,
    db: Session,
    kb_version_id: int,
    channel: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Run compliance checks driven entirely by the active KB version's data."""
    findings: List[Dict[str, Any]] = []
    lowered = text.lower()
    now = utc_now()

    # -------------------------------------------------------------
    # 0. Prompt-Injection / Adversarial Defense (Platform Safety)
    # -------------------------------------------------------------
    for pattern_str in INJECTION_PATTERNS:
        if pattern_str in lowered:
            regex = re.compile(re.escape(pattern_str), re.IGNORECASE)
            for span in find_spans(text, regex):
                findings.append({
                    "category": "security",
                    "severity": "blocker",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {
                        "type": "security_policy",
                        "id": "SEC-INJECT-01",
                        "quote": "System prompt overrides and review bypass patterns are strictly blocked."
                    },
                    "reason": f"Adversarial prompt injection pattern detected: '{span['text']}'.",
                    "suggestion": {"text": "Remove prompt injection keywords and resubmit clean brand copy."},
                    "claim_status": "n/a",
                    "source": "rule",
                })

    # -------------------------------------------------------------
    # 1. Terminology Checks from Active KB Terms
    # -------------------------------------------------------------
    kb_terms = db.query(models.Term).filter(models.Term.kb_version_id == kb_version_id).all()
    
    # Also fetch active KB rules for linking rule codes
    kb_rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb_version_id).all()
    rule_code_by_cat = {r.category: r.code for r in kb_rules}

    for term in kb_terms:
        preferred = term.preferred
        term_rule_code = rule_code_by_cat.get("terminology", "KB-TERM-01")

        # Check banned variants
        banned_list = term.banned or []
        for banned_variant in banned_list:
            banned_str = str(banned_variant).strip()
            if not banned_str:
                continue
            regex = re.compile(rf"\b{re.escape(banned_str)}\b", re.IGNORECASE)
            for span in find_spans(text, regex):
                findings.append({
                    "category": "terminology",
                    "severity": "major",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {
                        "type": "term",
                        "id": term_rule_code,
                        "quote": f"Preferred nomenclature: '{preferred}'. Banned variant: '{banned_str}'."
                    },
                    "reason": f"Banned terminology '{span['text']}' used instead of approved brand term '{preferred}'.",
                    "suggestion": {"text": f"Replace with approved term '{preferred}'."},
                    "claim_status": "n/a",
                    "source": "rule",
                })

        # Check case rule if specified
        if term.case_rule == "exact" and preferred.lower() in lowered:
            # Look for instances of preferred text with wrong case
            regex_case = re.compile(rf"\b{re.escape(preferred)}\b", re.IGNORECASE)
            for span in find_spans(text, regex_case):
                if span["text"] != preferred:
                    findings.append({
                        "category": "terminology",
                        "severity": "minor",
                        "confidence": 0.95,
                        "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                        "evidence": {
                            "type": "term",
                            "id": term_rule_code,
                            "quote": f"Exact case requirement: '{preferred}'"
                        },
                        "reason": f"Brand term '{span['text']}' does not match exact required capitalisation '{preferred}'.",
                        "suggestion": {"text": preferred},
                        "claim_status": "n/a",
                        "source": "rule",
                    })

    # -------------------------------------------------------------
    # 2. Rule Checks from Active KB Rules
    # -------------------------------------------------------------
    for rule in kb_rules:
        # Channel filter
        if rule.channels and channel and channel not in rule.channels:
            continue

        category = rule.category
        rule_code = rule.code
        severity = rule.severity_default or "major"

        # Check bad examples
        bad_examples = rule.examples_bad or []
        for bad_ex in bad_examples:
            bad_str = str(bad_ex).strip()
            if not bad_str:
                continue

            # Check exact or regex substring
            found_spans = []
            try:
                rx = re.compile(rf"\b{re.escape(bad_str)}\b", re.IGNORECASE)
                found_spans = find_spans(text, rx)
            except Exception:
                pass

            if not found_spans and bad_str.lower() in lowered:
                rx = re.compile(re.escape(bad_str), re.IGNORECASE)
                found_spans = find_spans(text, rx)

            # If still not found, try fuzzy match on sentences
            if not found_spans and len(bad_str) > 15:
                # Split text into rough sentence chunks
                chunks = re.finditer(r"[^.!?\n]+[.!?\n]?", text)
                for chunk in chunks:
                    chunk_text = chunk.group(0).strip()
                    if chunk_text:
                        ratio = fuzz.partial_ratio(bad_str.lower(), chunk_text.lower())
                        if ratio >= 90:
                            found_spans.append({"start": chunk.start(), "end": chunk.end(), "text": chunk_text})

            for span in found_spans:
                sugg_text = ""
                if rule.examples_good and len(rule.examples_good) > 0:
                    sugg_text = f"Consider approved alternative: '{rule.examples_good[0]}'."
                else:
                    sugg_text = f"Revise to comply with {rule_code}: {rule.text}"

                findings.append({
                    "category": category,
                    "severity": severity,
                    "confidence": 0.95,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {
                        "type": "rule",
                        "id": rule_code,
                        "quote": rule.text,
                    },
                    "reason": f"Violates brand guideline [{rule_code}]: {rule.text}",
                    "suggestion": {"text": sugg_text},
                    "claim_status": "n/a",
                    "source": "rule",
                })

    # -------------------------------------------------------------
    # 3. Numeric & Date Fact Checking from Active KB Facts
    # -------------------------------------------------------------
    kb_facts = db.query(models.Fact).filter(models.Fact.kb_version_id == kb_version_id).all()
    extracted_nums = extract_numbers_with_context(text)

    for fact in kb_facts:
        fact_val_clean = fact.value.replace(",", "").strip()
        fact_unit = (fact.unit or "").lower().strip()
        fact_key_words = [w for w in re.split(r"[_\s]+", fact.key.lower()) if len(w) > 2]
        is_stale = bool(fact.valid_to and fact.valid_to < now)

        try:
            fact_num = float(fact_val_clean)
        except ValueError:
            fact_num = None

        if fact_num is not None:
            for item in extracted_nums:
                # Check if this extracted number is describing this fact's entity
                # Match condition: matching unit OR fact key words appear in surrounding context
                unit_matches = fact_unit and (fact_unit in item["unit"] or item["unit"] in fact_unit)
                context_matches = any(kw in item["context"] for kw in fact_key_words)

                if unit_matches or context_matches:
                    # Compare numerical value
                    if abs(item["val"] - fact_num) > 1e-4:
                        claim_st = "outdated" if is_stale else "contradicted"
                        reason = (
                            f"Contradicts approved fact [{fact.code}]: '{fact.key}' is officially "
                            f"{fact.value} {fact.unit or ''} (source: {fact.source or 'Brand Knowledge Base'}), "
                            f"but content states {item['text']}."
                        )
                        if is_stale:
                            reason = f"Cites outdated/expired fact [{fact.code}]: expired on {fact.valid_to.strftime('%Y-%m-%d')}."

                        findings.append({
                            "category": "messaging",
                            "severity": "major",
                            "confidence": 0.94,
                            "span": {"start": item["start"], "end": item["end"], "text": item["text"]},
                            "evidence": {
                                "type": "fact",
                                "id": fact.code,
                                "quote": f"{fact.key}: {fact.value} {fact.unit or ''} ({fact.source or 'Approved KB'})",
                            },
                            "reason": reason,
                            "suggestion": {
                                "text": f"Update to approved specification: {fact.value} {fact.unit or ''}"
                            },
                            "claim_status": claim_st,
                            "source": "rule",
                        })

    # -------------------------------------------------------------
    # 4. Promotional Claim & Disclaimer Checks from Active KB Claims
    # -------------------------------------------------------------
    kb_claims = db.query(models.Claim).filter(models.Claim.kb_version_id == kb_version_id).all()

    # Generic unbacked superlative / guarantee triggers
    SUPERLATIVE_PATTERNS = [
        (r"\b(guarantee\w*|100%\s+safe|cure\w*|melt fat|instant six-pack)\b", "NF-CLAIM-01", "Unsubstantiated or prohibited guarantee/health claim."),
        (r"\b(zero risk|double your wealth|no chance of loss|guaranteed 0%|risk-free equity)\b", "LB-REG-01", "Unsubstantiated risk-free investment or lending claim."),
        (r"\b(ranked #1 in the universe|guaranteed immediate employment|best university in human history)\b", "AU-TONE-01", "Unsubstantiated hyperbolic ranking or outcome claim."),
        (r"\b(cheapest\s+[a-z]+|#1\s+[a-z]+|best\s+[a-z]+|free\s+forever)\b", "KB-CLAIM-01", "Unverified superlative ranking or pricing claim."),
    ]

    # Evaluate against approved claims register
    from ..claims.ledger import evaluate_claims
    claim_items = evaluate_claims(text, kb_claims)

    for item in claim_items:
        c_status = item["status"]
        if c_status in ("missing_disclaimer", "expired", "unsupported", "outdated", "contradicted"):
            sev = "blocker" if any(w in item["claim_text"].lower() for w in ["guarantee", "cure", "risk-free", "zero risk", "100%"]) else "major"
            rule_id = rule_code_by_cat.get("claim", "KB-CLAIM-01")

            sugg_text = ""
            if c_status == "missing_disclaimer" and item.get("required_disclaimer"):
                sugg_text = f"Append mandatory disclaimer: '{item['required_disclaimer']}'"
            elif c_status in ("expired", "outdated"):
                sugg_text = "Remove expired promotional claim or refresh substantiate evidence."
            else:
                sugg_text = "Qualify claim or provide verifiable substantiation on file."

            findings.append({
                "category": "claim",
                "severity": sev,
                "confidence": 0.95,
                "span": {"start": item["span_start"], "end": item["span_end"], "text": item["claim_text"]},
                "evidence": {
                    "type": "claim",
                    "id": item.get("evidence_ref") or rule_id,
                    "quote": item.get("approved_text") or item["claim_text"],
                },
                "reason": item["reason"],
                "suggestion": {"text": sugg_text},
                "claim_status": c_status,
                "source": "rule",
            })

    # Check remaining superlatives if not already caught
    for pat, fallback_rule, reason_str in SUPERLATIVE_PATTERNS:
        rx = re.compile(pat, re.IGNORECASE)
        for span in find_spans(text, rx):
            # Check if this span overlaps with an existing finding
            already_covered = any(
                f["span"]["start"] <= span["start"] and f["span"]["end"] >= span["end"]
                for f in findings if f["category"] == "claim"
            )
            if not already_covered:
                rule_id = rule_code_by_cat.get("claim", fallback_rule)
                findings.append({
                    "category": "claim",
                    "severity": "blocker",
                    "confidence": 0.96,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {
                        "type": "rule",
                        "id": rule_id,
                        "quote": "Claims must be substantiated with verified evidence on file."
                    },
                    "reason": reason_str,
                    "suggestion": {"text": "Remove unconditional guarantee or provide approved evidence reference."},
                    "claim_status": "unsupported",
                    "source": "rule",
                })

    return findings
