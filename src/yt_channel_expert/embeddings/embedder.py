from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import numpy as np

class Embedder(ABC):
    @property
    @abstractmethod
    def dim(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Return embeddings array of shape (len(texts), dim)."""
        raise NotImplementedError
