from __future__ import annotations
from typing import Any, Dict, Iterator, List, Optional

from .base import LLMBackend, Message


class LLMHubLocalBackend(LLMBackend):
    """Calls the local llmhub Python package in-process."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        temperature: float = 0.2,
        top_p: Optional[float] = None,
        max_tokens: int = 512,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = _normalize_provider(provider)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.extra = extra or {}

        self._hub = _build_hub(self.provider, self.extra)

        self.last_usage: Optional[Dict[str, Any]] = None
        self.last_finish_reason: Optional[str] = None
        self.last_tool_calls: Optional[List[Dict[str, Any]]] = None

    def generate(self, messages: List[Message], *, tools=None, tool_choice=None, response_format=None) -> str:
        input_obj = _build_generate_input(
            provider=self.provider,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            metadata=self.extra.get("metadata"),
        )
        output = self._hub.generate(input_obj)
        return _normalize_output(self, output)

    def stream_generate(
        self,
        messages: List[Message],
        *,
        tools=None,
        tool_choice=None,
        response_format=None,
    ) -> Iterator[str]:
        input_obj = _build_generate_input(
            provider=self.provider,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            metadata=self.extra.get("metadata"),
        )
        for chunk in self._hub.stream_generate(input_obj):
            if getattr(chunk, "type", None) == "delta" and getattr(chunk, "textDelta", None):
                yield chunk.textDelta
            elif getattr(chunk, "type", None) == "message_end":
                self.last_usage = _usage_to_dict(getattr(chunk, "usage", None))
                self.last_finish_reason = getattr(chunk, "finishReason", None)
            elif getattr(chunk, "type", None) == "error":
                raise RuntimeError(f"llmhub local stream error: {getattr(chunk, 'error', None)}")


def _build_generate_input(
    *,
    provider: str,
    model: str,
    messages: List[Message],
    temperature: float,
    top_p: Optional[float],
    max_tokens: int,
    tools: Optional[list[dict]],
    tool_choice: Optional[object],
    response_format: Optional[dict],
    metadata: Optional[Dict[str, str]],
):
    try:
        from llmhub.types import GenerateInput
    except ImportError as exc:
        raise ImportError("llmhub package is required for local llmhub backend") from exc

    return GenerateInput(
        provider=provider,
        model=model,
        messages=messages,
        tools=tools,
        toolChoice=tool_choice,
        responseFormat=response_format,
        temperature=temperature,
        topP=top_p,
        maxTokens=max_tokens,
        metadata=metadata,
    )


def _normalize_output(self_ref: "LLMHubLocalBackend", output: Any) -> str:
    text = getattr(output, "text", None)
    tool_calls = getattr(output, "toolCalls", None)
    usage = getattr(output, "usage", None)
    finish_reason = getattr(output, "finishReason", None)

    self_ref.last_usage = _usage_to_dict(usage)
    self_ref.last_finish_reason = finish_reason
    self_ref.last_tool_calls = _tool_calls_to_dict(tool_calls)

    if tool_calls:
        raise RuntimeError("llmhub tool calls are not supported by this package yet")
    return text or ""


def _usage_to_dict(usage: Any) -> Optional[Dict[str, Any]]:
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage
    data = {}
    for key in ("inputTokens", "outputTokens", "totalTokens"):
        value = getattr(usage, key, None)
        if value is not None:
            data[key] = value
    return data or None


def _tool_calls_to_dict(tool_calls: Any) -> Optional[List[Dict[str, Any]]]:
    if tool_calls is None:
        return None
    if isinstance(tool_calls, list):
        out: List[Dict[str, Any]] = []
        for call in tool_calls:
            if isinstance(call, dict):
                out.append(call)
            else:
                out.append({
                    "id": getattr(call, "id", None),
                    "name": getattr(call, "name", None),
                    "argumentsJson": getattr(call, "argumentsJson", None),
                })
        return out
    return None



def _normalize_provider(provider: str) -> str:
    p = provider.lower()
    if p == "gemini":
        return "google"
    return p


def _build_hub(default_provider: str, extra: Dict[str, Any]):
    try:
        from llmhub import Hub, HubConfig
    except ImportError as exc:
        raise ImportError("llmhub package is required for local llmhub backend") from exc

    providers_cfg = extra.get("providers")
    if isinstance(providers_cfg, dict) and providers_cfg:
        providers = _build_providers_from_dict(providers_cfg)
    else:
        providers = {
            default_provider: _build_provider_config(default_provider, extra),
        }

    return Hub(HubConfig(providers=providers))


def _build_providers_from_dict(providers_cfg: Dict[str, Any]) -> Dict[str, object]:
    providers: Dict[str, object] = {}
    for provider, cfg in providers_cfg.items():
        providers[_normalize_provider(provider)] = _build_provider_config(provider, cfg)
    return providers


def _build_provider_config(provider: str, cfg: Dict[str, Any]):
    provider_name = _normalize_provider(provider)
    cfg = dict(cfg)
    if "timeout" not in cfg and "timeout_s" in cfg:
        cfg["timeout"] = cfg.get("timeout_s")

    try:
        from llmhub.providers import OpenAIConfig, AnthropicConfig, GeminiConfig, XAIConfig
    except ImportError as exc:
        raise ImportError("llmhub package is required for local llmhub backend") from exc

    config_map = {
        "openai": (OpenAIConfig, {"api_key", "api_keys", "base_url", "organization", "default_use_responses", "timeout"}),
        "anthropic": (AnthropicConfig, {"api_key", "api_keys", "base_url", "version", "timeout"}),
        "google": (GeminiConfig, {"api_key", "api_keys", "base_url", "timeout"}),
        "xai": (XAIConfig, {"api_key", "api_keys", "base_url", "compatibility_mode", "timeout"}),
    }

    if provider_name not in config_map:
        raise ValueError(f"Unsupported llmhub provider: {provider_name}")

    cls, allowed = config_map[provider_name]
    kwargs = {k: cfg[k] for k in allowed if k in cfg and cfg[k] is not None}
    return cls(**kwargs)
