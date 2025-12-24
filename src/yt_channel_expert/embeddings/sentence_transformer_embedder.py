from __future__ import annotations
from typing import List
import numpy as np
from .embedder import Embedder

class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("sentence-transformers not installed. pip install -e '.[embeddings]'") from e
        self._model = SentenceTransformer(model_name)
        # Infer dim from model by embedding a tiny string
        v = self._model.encode(["test"], normalize_embeddings=True)
        self._dim = int(v.shape[1])

    @property
    def dim(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        v = self._model.encode(texts, normalize_embeddings=True)
        return np.asarray(v, dtype=np.float32)
