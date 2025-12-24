from __future__ import annotations
from typing import List
from .base import LLMBackend, Message
from ..rag.prompts import messages_to_debug_prompt

class LlamaCppBackend(LLMBackend):
    def __init__(self, model_path: str, n_ctx: int = 4096, max_tokens: int = 512, temperature: float = 0.2):
        try:
            from llama_cpp import Llama  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("llama-cpp-python not installed. pip install -e '.[llama_cpp]'") from e

        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            verbose=False,
        )
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> str:
        prompt = messages_to_debug_prompt(messages)
        out = self.llm(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=[],
        )
        return out["choices"][0]["text"]
