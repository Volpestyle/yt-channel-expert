from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import numpy as np

from .vector_index import VectorIndex, VectorHit
from .bm25 import BM25, BM25Hit

@dataclass
class HybridHit:
    idx: int
    score: float
    sources: Tuple[str, ...]

class HybridRetriever:
    def __init__(
        self,
        vector_index: VectorIndex,
        bm25: Optional[BM25] = None,
        alpha: float = 0.7,
    ) -> None:
        self.vector_index = vector_index
        self.bm25 = bm25
        self.alpha = alpha

    def search(self, query_vec: np.ndarray, query_text: str, top_k: int, bm25_top_k: int = 20) -> List[HybridHit]:
        vec_hits = self.vector_index.search(query_vec, top_k=top_k)
        bm_hits: List[BM25Hit] = self.bm25.search(query_text, top_k=bm25_top_k) if self.bm25 else []

        # Normalize scores to [0,1] within each list
        def norm(scores: List[float]) -> List[float]:
            if not scores:
                return []
            mx = max(scores)
            mn = min(scores)
            if abs(mx - mn) < 1e-9:
                return [1.0 for _ in scores]
            return [(s - mn) / (mx - mn) for s in scores]

        vec_norm = norm([h.score for h in vec_hits])
        bm_norm = norm([h.score for h in bm_hits])

        agg: Dict[int, HybridHit] = {}
        for h, s in zip(vec_hits, vec_norm):
            agg[h.idx] = HybridHit(idx=h.idx, score=self.alpha * s, sources=("vector",))
        for h, s in zip(bm_hits, bm_norm):
            if h.idx in agg:
                prev = agg[h.idx]
                agg[h.idx] = HybridHit(idx=h.idx, score=prev.score + (1 - self.alpha) * s, sources=tuple(sorted(set(prev.sources + ("bm25",)))))
            else:
                agg[h.idx] = HybridHit(idx=h.idx, score=(1 - self.alpha) * s, sources=("bm25",))

        hits = list(agg.values())
        hits.sort(key=lambda x: x.score, reverse=True)
        return hits[:top_k]
