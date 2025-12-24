# LLM runtimes (local + API) with llmhub-node

This repo’s `LLMBackend` interface is message-based and intentionally mirrors the llmhub-node request shape.

## Recommended path: llmhub-node over HTTP

Run llmhub as a small HTTP server (local or remote) and configure this Python package to call it.

- Python adapter: `src/yt_channel_expert/llm/llmhub_http.py`
- Endpoints:
  - `POST /generate`
  - `POST /generate/stream` (SSE)

Config keys (in `llm.extra`):
- `base_url` (default `http://localhost:8787`)
- `timeout_s`
- `verify_tls`

## Included backends

- `MockLLM` (tests)
- `LlamaCppBackend` (requires `llama-cpp-python`)
- `MLXBackend` (requires `mlx-lm`, macOS only)
- `LLMHubHTTPBackend` (**recommended**) (calls llmhub-node server)
