# Testing and evaluation

## Unit tests

- transcript parsing (SRT/VTT/JSON)
- micro-chunk boundaries
- section creation (chapter parsing + auto-chapter)
- deterministic retrieval with `HashEmbedder`

## Offline evaluation harness

Suggested eval types:
- **timestamp retrieval**: ask “where did they say X” and measure top-k hit rate
- **stance summarization**: compare answers vs reference summaries
- **citation coverage**: ensure % of paragraphs have citations

The `eval/` module includes a small framework to add datasets and compute metrics.
