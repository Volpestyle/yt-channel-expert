# llmhub-node integration (Hub + HTTP handlers)

You provided the llmhub-node API shape:

- `createHub({ providers })`
- `hub.generate({ provider, model, messages, ... })`
- `hub.streamGenerate(...)`
- `httpHandlers(hub)` exposing:
  - `GET /provider-models`
  - `POST /generate`
  - `POST /generate/stream` (SSE)

## How this repo uses it

This Python repo owns:

- pack building (SQLite + embeddings + sections)
- retrieval (hybrid)
- prompt/message assembly (system rules + evidence snippets)
- citation enforcement

Then it calls llmhub for generation.

### Why this split works well

- Swap providers/models without touching RAG.
- Run llmhub locally (Mac) or remotely.
- Use API models or local models if llmhub supports them.

## Python adapter

See: `src/yt_channel_expert/llm/llmhub_http.py`

- non-streaming: POST `/generate`
- streaming: POST `/generate/stream` and parse SSE chunks:
  - `{ type:"delta", textDelta:"..." }`
  - `{ type:"message_end", ... }`
  - `{ type:"error", error:{...} }`

## Message format

This repo emits messages:

```json
[
  {"role":"system","content":[{"type":"text","text":"...rules..."}]},
  {"role":"user","content":[{"type":"text","text":"...question + evidence..."}]}
]
```

## Config example

```json
{
  "llm": {
    "backend": "llmhub",
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.2,
    "max_new_tokens": 600,
    "extra": { "base_url": "http://localhost:8787", "timeout_s": 90 }
  }
}
```


## GenerateOutput

llmhub-node returns:

```ts
interface GenerateOutput {
  text?: string;
  toolCalls?: { id: string; name: string; argumentsJson: string }[];
  usage?: { inputTokens?: number; outputTokens?: number; totalTokens?: number };
  finishReason?: string;
}
```

Next: `docs/14_consuming_apps.md`.
