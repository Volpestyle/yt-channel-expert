# llmhub_server (optional)

A minimal Node server that hosts your llmhub Hub behind HTTP endpoints so the Python RAG package can call:

- `POST /generate`
- `POST /generate/stream` (SSE)
- `GET /provider-models`

## Install + run

```bash
cd services/llmhub_server
npm install
export OPENAI_API_KEY=...
npm run dev
```

Defaults to `http://localhost:8787`.
