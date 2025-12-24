from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, Dict, Any
import yaml

class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    backend: Literal["hash", "sentence_transformer"] = "hash"
    model_name: str = "hash-384"
    dim: int = 384

class LLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    backend: Literal["mock", "llama_cpp", "mlx", "llmhub"] = "mock"

    # Local backends
    model_path: Optional[str] = None

    # llmhub backend
    provider: Optional[str] = None
    model: Optional[str] = None

    context_tokens: int = 4096
    max_new_tokens: int = 512
    temperature: float = 0.2
    top_p: Optional[float] = None

    # For llmhub backend, recommended keys:
    #   base_url: "http://localhost:8787"
    #   timeout_s: 60
    #   verify_tls: true
    extra: Dict[str, Any] = Field(default_factory=dict)

class ChunkingConfig(BaseModel):
    micro_chunk_sec: int = 45
    micro_overlap_sec: int = 15
    target_section_sec: int = 7 * 60
    max_section_sec: int = 12 * 60

class RetrievalConfig(BaseModel):
    top_sections: int = 5
    top_chunks: int = 10
    use_bm25: bool = True
    bm25_top_k: int = 20

class PackConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    schema_version: int = 1
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

def load_config(path: str) -> PackConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return PackConfig.model_validate(data)
