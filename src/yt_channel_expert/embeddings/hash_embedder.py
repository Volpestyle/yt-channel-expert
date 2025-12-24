from __future__ import annotations
import hashlib
from typing import List
import numpy as np
from .embedder import Embedder

class HashEmbedder(Embedder):
    """Deterministic lightweight embedding using feature hashing.

    This is NOT a semantic embedding model. It's a fallback that:
    - is fast,
    - deterministic,
    - avoids heavy dependencies,
    - allows testing the pipeline end-to-end.

    Replace with SentenceTransformerEmbedder or another production embedder.
    """
    def __init__(self, dim: int = 384):
        self._dim = int(dim)

    @property
    def dim(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        mat = np.zeros((len(texts), self._dim), dtype=np.float32)
        for i, t in enumerate(texts):
            # simple tokenization
            for token in t.lower().split():
                h = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(h[:4], "little") % self._dim
                sign = 1.0 if (h[4] % 2 == 0) else -1.0
                mat[i, idx] += sign
        # normalize
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
        mat = mat / norms
        return mat
