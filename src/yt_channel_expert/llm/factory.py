from __future__ import annotations
from ..config import LLMConfig
from .base import LLMBackend
from .mock import MockLLM

def make_llm(cfg: LLMConfig) -> LLMBackend:
    if cfg.backend == "mock":
        return MockLLM()

    if cfg.backend == "llmhub":
        if not cfg.provider or not cfg.model:
            raise ValueError("llm.provider and llm.model are required for llmhub backend")
        mode = str(cfg.extra.get("mode", "http")).lower()
        if mode in ("local", "python", "inprocess"):
            from .llmhub_local import LLMHubLocalBackend
            return LLMHubLocalBackend(
                provider=cfg.provider,
                model=cfg.model,
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                max_tokens=cfg.max_new_tokens,
                extra=cfg.extra,
            )

        base_url = str(cfg.extra.get("base_url", "http://localhost:8787"))
        timeout_s = float(cfg.extra.get("timeout_s", 60))
        verify_tls = bool(cfg.extra.get("verify_tls", True))

        from .llmhub_http import LLMHubHTTPBackend
        return LLMHubHTTPBackend(
            base_url=base_url,
            provider=cfg.provider,
            model=cfg.model,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            max_tokens=cfg.max_new_tokens,
            timeout_s=timeout_s,
            verify_tls=verify_tls,
            extra=cfg.extra,
        )

    if cfg.backend == "llama_cpp":
        if not cfg.model_path:
            raise ValueError("llm.model_path required for llama_cpp backend")
        from .llama_cpp import LlamaCppBackend
        return LlamaCppBackend(
            model_path=cfg.model_path,
            n_ctx=cfg.context_tokens,
            max_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
        )

    if cfg.backend == "mlx":
        if not cfg.model_path:
            raise ValueError("llm.model_path required for mlx backend")
        from .mlx import MLXBackend
        return MLXBackend(
            model_path=cfg.model_path,
            max_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
        )

    raise ValueError(f"Unknown llm backend: {cfg.backend}")
