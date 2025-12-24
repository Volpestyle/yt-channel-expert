# Repository layout

```
yt-channel-expert/
  docs/                       # Design spec & implementation notes (this folder)
  examples/                   # Demo input data for pack builder
  scripts/                    # Helper scripts (thin wrappers around library)
  src/yt_channel_expert/      # Python package
  tests/                      # Unit tests (focus on chunking/retrieval determinism)
```

## Package modules

- `yt_channel_expert.ingestion.*`  
  Load channel/video metadata and transcripts (from authorized sources).

- `yt_channel_expert.processing.*`  
  Normalize transcripts, create micro-chunks and sections, auto-chapter, summarization.

- `yt_channel_expert.embeddings.*`  
  Embedding backends (hash fallback, sentence-transformers optional).

- `yt_channel_expert.index.*`  
  Vector and keyword indexing + hybrid retrieval.

- `yt_channel_expert.pack.*`  
  Channel Pack schema, build/read utilities.

- `yt_channel_expert.rag.*`  
  Retrieval + prompt assembly + answer synthesis + citation formatting.

- `yt_channel_expert.llm.*`  
  Local LLM runtime abstractions (mock; llama.cpp; MLX).

- `yt_channel_expert.cli.*`  
  `ytce` CLI.

See also: `docs/08_channel_pack_format.md`.
