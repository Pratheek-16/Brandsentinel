"""VectorStore interface and in-process retrieval implementation.
Provides vector indexing, retrieval, and embedding caching for KB rules, facts, and claims.
Includes BM25-style keyword scoring fallback with channel and validity filters.
Deterministic and repeatable across test and production environments.
"""

import math
import hashlib
import datetime
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def tokenize(text: str) -> List[str]:
    """Simple lowercase word tokenizer."""
    return [w for w in re.findall(r"\b\w{2,}\b", text.lower())]

def compute_keyword_relevance(query_tokens: List[str], doc_text: str) -> float:
    """Compute normalized token overlap score between query and document text."""
    if not query_tokens or not doc_text:
        return 0.0
    doc_tokens = set(tokenize(doc_text))
    if not doc_tokens:
        return 0.0
    matches = sum(1 for q in query_tokens if q in doc_tokens)
    return matches / max(1, len(set(query_tokens)))

class VectorStore:
    def __init__(self):
        # item_id -> {"vector": List[float], "metadata": dict}
        self._index: Dict[str, Dict[str, Any]] = {}
        # text_hash -> List[float]
        self._cache: Dict[str, List[float]] = {}

    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return self._cache.get(h)

    def cache_embedding(self, text: str, vector: List[float]) -> None:
        h = hashlib.sha256(text.encode()).hexdigest()
        self._cache[h] = vector

    def upsert(self, item_id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        self._index[item_id] = {
            "vector": vector,
            "metadata": metadata,
        }

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter_fn: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for item_id, item in self._index.items():
            if filter_fn and not filter_fn(item["metadata"]):
                continue
            sim = cosine_similarity(vector, item["vector"])
            results.append({
                "id": item_id,
                "score": sim,
                "metadata": item["metadata"],
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def retrieve_evidence_for_segment(
        self,
        segment_text: str,
        db: Session,
        kb_version_id: int,
        top_k: int = 5,
        channel: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant KB rules, facts, claims, and terms for a text segment.
        Uses keyword relevance (BM25-style token overlap) and date/channel validity filtering.
        """
        from ...db import models
        query_tokens = tokenize(segment_text)
        now = datetime.datetime.utcnow()
        candidates = []

        # 1. Rules
        rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb_version_id).all()
        for r in rules:
            if r.channels and channel and channel not in r.channels:
                continue
            combined_text = f"{r.text} {' '.join(r.examples_bad or [])} {' '.join(r.examples_good or [])}"
            score = compute_keyword_relevance(query_tokens, combined_text)
            if score > 0.05 or len(candidates) < 3:
                candidates.append({
                    "type": "rule",
                    "id": r.code,
                    "category": r.category,
                    "text": r.text,
                    "score": score + 0.1,  # slight rule priority
                })

        # 2. Facts (filtered by validity)
        facts = db.query(models.Fact).filter(models.Fact.kb_version_id == kb_version_id).all()
        for f in facts:
            # Check validity dates
            if f.valid_to and f.valid_to < now:
                # Include as outdated candidate if fact key appears in text
                score = compute_keyword_relevance(query_tokens, f"{f.key} {f.value} {f.unit or ''}")
                if score > 0.1:
                    candidates.append({
                        "type": "fact",
                        "id": f.code,
                        "key": f.key,
                        "value": f.value,
                        "text": f"{f.key}: {f.value} {f.unit or ''} (Expired on {f.valid_to.strftime('%Y-%m-%d')})",
                        "score": score,
                        "is_outdated": True,
                    })
            else:
                score = compute_keyword_relevance(query_tokens, f"{f.key} {f.value} {f.unit or ''}")
                if score > 0.05:
                    candidates.append({
                        "type": "fact",
                        "id": f.code,
                        "key": f.key,
                        "value": f.value,
                        "text": f"{f.key}: {f.value} {f.unit or ''}",
                        "score": score,
                        "is_outdated": False,
                    })

        # 3. Claims
        claims = db.query(models.Claim).filter(models.Claim.kb_version_id == kb_version_id).all()
        for c in claims:
            score = compute_keyword_relevance(query_tokens, c.approved_text)
            if score > 0.05:
                candidates.append({
                    "type": "claim",
                    "id": c.evidence_ref or f"CLAIM-{c.id}",
                    "text": c.approved_text,
                    "disclaimer": c.required_disclaimer,
                    "score": score,
                })

        # 4. Terms
        terms = db.query(models.Term).filter(models.Term.kb_version_id == kb_version_id).all()
        for t in terms:
            term_text = f"{t.preferred} {' '.join(t.banned or [])}"
            score = compute_keyword_relevance(query_tokens, term_text)
            if score > 0.05:
                candidates.append({
                    "type": "term",
                    "id": t.preferred,
                    "text": f"Preferred: '{t.preferred}', Banned: {', '.join(t.banned or [])}",
                    "score": score + 0.15,
                })

        # Sort descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

# Global shared instance
global_vector_store = VectorStore()
