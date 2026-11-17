"""VectorStore interface and in-process Cosine Similarity implementation.
Provides vector indexing, retrieval, and embedding caching for KB rules, facts, and claims.
Compatible with SQLite local fallback and pgvector in PostgreSQL deployment.
"""

import math
import hashlib
from typing import List, Dict, Any, Optional

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

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

# Global shared instance for local memory/dev
global_vector_store = VectorStore()
