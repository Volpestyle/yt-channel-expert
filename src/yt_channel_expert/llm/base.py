from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, TypedDict, Literal

Role = Literal["system", "user", "assistant", "tool"]

class TextPart(TypedDict):
    type: Literal["text"]
    text: str

class Message(TypedDict):
    role: Role
    content: List[TextPart]

class LLMBackend(ABC):
    """Unified LLM interface (local + API) using chat-style messages.

    This intentionally matches your `llmhub-node` GenerateInput shape:
      - messages: [{ role, content: [{type:'text', text:'...'}] }]
      - optional tools/toolChoice/responseFormat
      - optional streaming
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        *,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[object] = None,
        response_format: Optional[dict] = None,
    ) -> str:
        raise NotImplementedError

    def stream_generate(
        self,
        messages: List[Message],
        *,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[object] = None,
        response_format: Optional[dict] = None,
    ) -> Iterator[str]:
        """Default streaming: yield the full completion once."""
        yield self.generate(messages, tools=tools, tool_choice=tool_choice, response_format=response_format)
