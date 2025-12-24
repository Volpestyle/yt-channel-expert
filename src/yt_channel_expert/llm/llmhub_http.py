from __future__ import annotations
from typing import Any, Dict, Iterator, List, Optional
import json
import urllib.request
import urllib.error
import ssl

from .base import LLMBackend, Message

class LLMHubHTTPBackend(LLMBackend):
    """Calls a running llmhub-node HTTP server.

    Endpoints:
      - POST /generate
      - POST /generate/stream  (SSE: text/event-stream)
      - GET  /provider-models

    Payload matches llmhub-node `GenerateInput`:
      { provider, model, messages, tools?, toolChoice?, responseFormat?, temperature?, topP?, maxTokens? }

    Non-streaming output matches your `GenerateOutput`:
      {
        text?: string;
        toolCalls?: { id: string; name: string; argumentsJson: string }[];
        usage?: { inputTokens?: number; outputTokens?: number; totalTokens?: number };
        finishReason?: string;
      }

    This backend returns only `text` from `GenerateOutput`. If toolCalls are returned,
    it raises (tool execution is not implemented in this repo yet).
    """

    def __init__(
        self,
        *,
        base_url: str,
        provider: str,
        model: str,
        temperature: float = 0.2,
        top_p: Optional[float] = None,
        max_tokens: int = 512,
        timeout_s: float = 60.0,
        verify_tls: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self.verify_tls = verify_tls
        self.extra = extra or {}

        # Last-call metadata (best-effort)
        self.last_usage: Optional[Dict[str, Any]] = None
        self.last_finish_reason: Optional[str] = None
        self.last_tool_calls: Optional[List[Dict[str, Any]]] = None

    def generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> str:
        url = self.base_url + "/generate"
        payload: Dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }
        if self.top_p is not None:
            payload["topP"] = self.top_p
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["toolChoice"] = tool_choice
        if response_format is not None:
            payload["responseFormat"] = response_format

        payload.update(self.extra.get("request_overrides", {}))

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
        ctx = None
        if url.startswith("https://") and not self.verify_tls:
            ctx = ssl._create_unverified_context()  # noqa: SslCertVerificationDisabled

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s, context=ctx) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
            raise RuntimeError(f"llmhub HTTPError {e.code}: {detail}") from e
        except Exception as e:
            raise RuntimeError(f"llmhub request failed: {e}") from e

        obj: Any
        try:
            obj = json.loads(body)
        except Exception:
            # Unexpected non-JSON response; return as-is
            return body

        if isinstance(obj, dict):
            self.last_usage = obj.get("usage")
            self.last_finish_reason = obj.get("finishReason")
            self.last_tool_calls = obj.get("toolCalls")

        return _normalize_generate_output(obj)

    def stream_generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> Iterator[str]:
        url = self.base_url + "/generate/stream"
        payload: Dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }
        if self.top_p is not None:
            payload["topP"] = self.top_p
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["toolChoice"] = tool_choice
        if response_format is not None:
            payload["responseFormat"] = response_format

        payload.update(self.extra.get("request_overrides", {}))

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
            },
        )
        ctx = None
        if url.startswith("https://") and not self.verify_tls:
            ctx = ssl._create_unverified_context()  # noqa: SslCertVerificationDisabled

        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout_s, context=ctx)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
            raise RuntimeError(f"llmhub HTTPError {e.code}: {detail}") from e

        buf: List[str] = []
        try:
            for raw in resp:
                line = raw.decode("utf-8", errors="ignore").rstrip("\n")
                if not line:
                    if buf:
                        event_data = "\n".join(buf)
                        buf.clear()
                        for out in self._handle_sse_event(event_data):
                            yield out
                    continue
                if line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    buf.append(line[len("data:"):].lstrip())
            if buf:
                event_data = "\n".join(buf)
                for out in self._handle_sse_event(event_data):
                    yield out
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def _handle_sse_event(self, event_data: str) -> List[str]:
        if event_data.strip() == "[DONE]":
            return []
        try:
            obj = json.loads(event_data)
        except Exception:
            # If server sends plain deltas as strings
            return [event_data]

        t = obj.get("type")
        if t == "delta":
            d = obj.get("textDelta", "")
            return [d] if d else []
        if t == "message_end":
            # Persist usage metadata if present
            self.last_usage = obj.get("usage")
            self.last_finish_reason = obj.get("finishReason")
            return []
        if t == "tool_call":
            # Tool calls are not supported in this repo yet.
            return []
        if t == "error":
            raise RuntimeError(f"llmhub stream error: {obj.get('error')}")
        return []

def _normalize_generate_output(obj: Any) -> str:
    """Normalize llmhub-node `GenerateOutput` into assistant text."""
    if isinstance(obj, str):
        return obj
    if not isinstance(obj, dict):
        return json.dumps(obj)

    # Exact contract: { text?, toolCalls?, usage?, finishReason? }
    if "text" in obj and isinstance(obj["text"], str):
        return obj["text"]

    tool_calls = obj.get("toolCalls")
    if tool_calls:
        raise RuntimeError(
            "llmhub returned toolCalls but tool execution is not implemented in this repo. "
            "Either disable tools (toolChoice='none') or implement tool handling."
        )

    # No text (and no tool calls): return empty string
    return ""
