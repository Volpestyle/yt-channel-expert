from __future__ import annotations
from typing import List

from ..types import RetrievedChunk, ms_to_timestamp
from ..llm.base import Message

SYSTEM_RULES_TEXT = """You are a channel-specific expert assistant.
Only answer using the provided evidence snippets from the channel pack.
If evidence is insufficient, say so and suggest what to add (which video/transcript is missing).

For every non-trivial claim, include a citation in the format:
  [video_id @ mm:ss-mm:ss]

Do not invent citations.
"""

def _text_message(role: str, text: str) -> Message:
    return {"role": role, "content": [{"type": "text", "text": text}]}

def build_messages(question: str, channel_title: str, sections: List[str], chunks: List[RetrievedChunk]) -> List[Message]:
    msgs: List[Message] = [_text_message("system", SYSTEM_RULES_TEXT)]

    user_lines: List[str] = []
    user_lines.append(f"Channel: {channel_title}")
    user_lines.append(f"Question: {question}")

    if sections:
        user_lines.append("")
        user_lines.append("Relevant sections (summaries):")
        for s in sections:
            user_lines.append(f"- {s}")

    if chunks:
        user_lines.append("")
        user_lines.append("Evidence snippets (verbatim transcript excerpts):")
        for c in chunks:
            a = ms_to_timestamp(c.start_ms)
            b = ms_to_timestamp(c.end_ms)
            user_lines.append(f"[{c.video_id} @ {a}-{b}] {c.text}")

    user_lines.append("")
    user_lines.append("Write the best possible answer. Use citations inline.")
    msgs.append(_text_message("user", "\n".join(user_lines)))
    return msgs

def messages_to_debug_prompt(messages: List[Message]) -> str:
    parts: List[str] = []
    for m in messages:
        text = "".join(p.get("text","") for p in m.get("content",[]) if p.get("type") == "text")
        parts.append(f"{m['role'].upper()}:\n{text}")
    parts.append("ASSISTANT:")
    return "\n\n".join(parts)
