from __future__ import annotations
from ..config import EmbeddingConfig
from .embedder import Embedder
from .hash_embedder import HashEmbedder

def make_embedder(cfg: EmbeddingConfig) -> Embedder:
    if cfg.backend == "hash":
        return HashEmbedder(dim=cfg.dim)
    if cfg.backend == "sentence_transformer":
        from .sentence_transformer_embedder import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder(model_name=cfg.model_name)
    raise ValueError(f"Unknown embedding backend: {cfg.backend}")
