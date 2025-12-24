from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

@dataclass
class VectorHit:
    idx: int
    score: float

class VectorIndex:
    def add(self, embeddings: np.ndarray) -> None:
        raise NotImplementedError

    def search(self, query_vec: np.ndarray, top_k: int) -> List[VectorHit]:
        raise NotImplementedError

class BruteForceIndex(VectorIndex):
    def __init__(self) -> None:
        self._mat: Optional[np.ndarray] = None

    def add(self, embeddings: np.ndarray) -> None:
        # Expect normalized embeddings for cosine similarity via dot product
        self._mat = embeddings.astype(np.float32, copy=True)

    def search(self, query_vec: np.ndarray, top_k: int) -> List[VectorHit]:
        if self._mat is None:
            return []
        q = query_vec.astype(np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        scores = (self._mat @ q.T).reshape(-1)  # cosine if normalized
        if top_k >= len(scores):
            idxs = np.argsort(-scores)
        else:
            idxs = np.argpartition(-scores, top_k)[:top_k]
            idxs = idxs[np.argsort(-scores[idxs])]
        return [VectorHit(int(i), float(scores[i])) for i in idxs]

class HNSWIndex(VectorIndex):
    def __init__(self, dim: int, space: str = "cosine") -> None:
        try:
            import hnswlib  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("hnswlib not installed. pip install -e '.[hnsw]'") from e
        self._hnswlib = hnswlib
        self._dim = dim
        self._index = hnswlib.Index(space=space, dim=dim)
        self._count = 0

    def add(self, embeddings: np.ndarray) -> None:
        n = embeddings.shape[0]
        self._index.init_index(max_elements=n, ef_construction=200, M=16)
        self._index.add_items(embeddings, ids=list(range(n)))
        self._index.set_ef(50)
        self._count = n

    def search(self, query_vec: np.ndarray, top_k: int) -> List[VectorHit]:
        if self._count == 0:
            return []
        labels, distances = self._index.knn_query(query_vec, k=top_k)
        labels = labels.reshape(-1)
        distances = distances.reshape(-1)
        # For cosine space, hnswlib returns distance; convert to similarity-ish score
        hits: List[VectorHit] = []
        for i, d in zip(labels, distances):
            score = 1.0 - float(d)
            hits.append(VectorHit(int(i), score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits
