from __future__ import annotations
from typing import List
from .base import LLMBackend, Message
from ..rag.prompts import messages_to_debug_prompt

class MockLLM(LLMBackend):
    """A deterministic 'LLM' for demos/tests.

    It doesn't actually understand; it just returns a tiny structured answer with citations if present.
    """

    def generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> str:
        import re
        prompt = messages_to_debug_prompt(messages)
        m = re.search(r"(\[[A-Za-z0-9_-]+\s*@\s*(?:\d\d:)?\d\d:\d\d-(?:\d\d:)?\d\d:\d\d\])", prompt)
        cite = m.group(1) if m else "[unknown @ 00:00-00:00]"
        return (
            "Based on the provided channel evidence, the creator emphasizes grounded, checklist-driven workflows "
            f"and tool simplicity. {cite}\n\n"
            "If you want a more detailed synthesis, ingest more transcripts and enable a real LLM backend. "
            f"{cite}"
        )
