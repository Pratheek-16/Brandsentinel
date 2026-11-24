"""Offline Semantic Review Engine for BrandSentinel.

Operates with ZERO external network dependencies or API keys.
Evaluates input text against the active Knowledge Base rules using:
1. Sentence-level boundary segmentation with character offsets.
2. Hybrid token-set and character n-gram cosine matching against `examples_bad`,
   `rule.text`, and contrastive suppression against `examples_good`.
3. Strict quotation and rule ID citations aligning with the Verifier.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from ...db import models


def segment_sentences_with_offsets(text: str) -> List[Tuple[str, int, int]]:
    """Segment text into non-empty sentences with precise [start, end) character offsets."""
    sentences = []
    # Match sentences ending with punctuation or double newlines, or trailing segment
    pattern = re.compile(r"([^.!?\n]+(?:[.!?]+|\n+|$))", re.UNICODE)
    for match in pattern.finditer(text):
        raw_sent = match.group(0)
        start = match.start()
        end = match.end()
        # Strip trailing/leading whitespace while adjusting offsets
        stripped = raw_sent.strip()
        if not stripped:
            continue
        leading_ws = len(raw_sent) - len(raw_sent.lstrip())
        trailing_ws = len(raw_sent) - len(raw_sent.rstrip())
        sent_start = start + leading_ws
        sent_end = end - trailing_ws
        sentences.append((text[sent_start:sent_end], sent_start, sent_end))
    return sentences


def get_char_ngrams(s: str, n: int = 3) -> set:
    """Extract character n-grams from a normalized string."""
    clean = re.sub(r"\s+", " ", s.lower().strip())
    if len(clean) < n:
        return {clean}
    return {clean[i : i + n] for i in range(len(clean) - n + 1)}


def ngram_jaccard_similarity(s1: str, s2: str, n: int = 3) -> float:
    """Compute character n-gram Jaccard similarity."""
    ng1 = get_char_ngrams(s1, n)
    ng2 = get_char_ngrams(s2, n)
    if not ng1 or not ng2:
        return 0.0
    intersection = len(ng1 & ng2)
    union = len(ng1 | ng2)
    return intersection / max(1, union)


def compute_semantic_similarity(candidate_sentence: str, reference_text: str) -> float:
    """Compute hybrid semantic similarity between candidate sentence and reference example."""
    if not candidate_sentence or not reference_text:
        return 0.0

    s1 = candidate_sentence.lower().strip()
    s2 = reference_text.lower().strip()

    # 1. Fast fuzzy token-set ratio
    token_set = fuzz.token_set_ratio(s1, s2) / 100.0
    if token_set < 0.35:
        # Fast rejection for unrelated text
        return token_set * 0.5

    # 2. Partial ratio (finds embedded phrases)
    partial = fuzz.partial_ratio(s1, s2) / 100.0

    # 3. Character 3-gram similarity
    ngram_sim = ngram_jaccard_similarity(s1, s2, n=3)

    # Weighted ensemble favoring token_set and partial
    score = (0.50 * token_set) + (0.30 * partial) + (0.20 * ngram_sim)
    return score


def run_semantic_checks(
    text: str,
    db: Session,
    kb_version_id: int,
    channel: Optional[str] = None,
    threshold: float = 0.62,
) -> List[Dict[str, Any]]:
    """Evaluates text against active KB rules using the offline semantic layer.

    Flags sentences that semantically resemble `examples_bad` or prohibited patterns
    described in active rules, while suppressing sentences resembling `examples_good`.
    """
    if not text or not text.strip():
        return []

    rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb_version_id).all()
    if not rules:
        return []

    sentences = segment_sentences_with_offsets(text)
    findings = []
    seen_spans = set()

    for sent_text, sent_start, sent_end in sentences:
        if len(sent_text.split()) < 2:
            continue  # Skip single-word fragments to minimize noise

        for rule in rules:
            if rule.channels and channel and channel not in rule.channels:
                continue

            examples_bad = rule.examples_bad or []
            examples_good = rule.examples_good or []

            # 1. Check positive alignment first (suppression check)
            is_good_alignment = False
            for ex_good in examples_good:
                if isinstance(ex_good, str):
                    good_sim = compute_semantic_similarity(sent_text, ex_good)
                    if good_sim >= 0.72:
                        is_good_alignment = True
                        break
            if is_good_alignment:
                continue  # Content aligns with approved positive guidance

            # 2. Match against bad examples
            best_match_bad = None
            best_score_bad = 0.0

            for ex_bad in examples_bad:
                if isinstance(ex_bad, str):
                    sim = compute_semantic_similarity(sent_text, ex_bad)
                    if sim > best_score_bad:
                        best_score_bad = sim
                        best_match_bad = ex_bad

            # 3. Also test against rule text for conceptual tone/claim triggers
            rule_text_sim = compute_semantic_similarity(sent_text, rule.text)

            # Effective score considers strongest bad-example match or high rule-text overlap
            effective_score = max(best_score_bad, rule_text_sim * 0.90)

            # Determine whether threshold is met
            if effective_score >= threshold:
                span_key = (sent_start, sent_end, rule.category)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                matched_ref = best_match_bad if best_score_bad >= threshold else rule.text
                reason = (
                    f"Matches guideline '{rule.code}': {rule.text} "
                    f"(semantically resembles prohibited phrasing: '{matched_ref}')"
                )

                # Default suggested replacement if good example exists
                suggested_text = None
                if examples_good and isinstance(examples_good[0], str):
                    suggested_text = examples_good[0]

                findings.append({
                    "category": rule.category,
                    "severity": rule.severity_default or "medium",
                    "confidence": round(effective_score, 2),
                    "span": {
                        "start": sent_start,
                        "end": sent_end,
                        "text": sent_text,
                    },
                    "evidence": {
                        "type": "rule",
                        "id": rule.code,
                        "quote": rule.text,
                    },
                    "reason": reason,
                    "suggestion": {"text": suggested_text} if suggested_text else None,
                    "source": "semantic",
                })

    return findings
