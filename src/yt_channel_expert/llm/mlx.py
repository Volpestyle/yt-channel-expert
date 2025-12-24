from __future__ import annotations
from typing import List
from .base import LLMBackend, Message
from ..rag.prompts import messages_to_debug_prompt

class MLXBackend(LLMBackend):
    def __init__(self, model_path: str, max_tokens: int = 512, temperature: float = 0.2):
        # mlx-lm API changes; treat as illustrative.
        try:
            from mlx_lm import load, generate  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("mlx-lm not installed. pip install -e '.[mlx]' (macOS only)") from e

        self.model, self.tokenizer = load(model_path)
        self._generate = generate
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> str:
        prompt = messages_to_debug_prompt(messages)
        return self._generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temp=self.temperature,
        )
