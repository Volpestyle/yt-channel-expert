# Embeddings and indexing

## Embedding backends

This repo ships with a deterministic **HashEmbedder** for:
- running tests without heavy model dependencies,
- stable deterministic retrieval in CI.

For real use, swap to:
- `SentenceTransformerEmbedder` (CPU/GPU; macOS friendly),
- or a platform-native embedding model (future: MLX/CoreML).

See `src/yt_channel_expert/embeddings/embedder.py`.

## Vector index

We provide two index strategies:

1. **BruteForceIndex** (default)  
   - Stores embeddings in a NumPy matrix.
   - Cosine similarity search in O(N).
   - Fine for small/medium packs.

2. **HNSWIndex** (optional)  
   - Requires `hnswlib`.
   - Much faster for large packs.

## Hybrid retrieval

Hybrid retrieval combines:
- vector search (semantic), and
- keyword BM25 (lexical).

This improves:
- names, product model numbers, rare words.

The hybrid retriever merges and deduplicates results, then optionally reranks.

See:
- `src/yt_channel_expert/index/vector_index.py`
- `src/yt_channel_expert/index/bm25.py`
- `src/yt_channel_expert/index/hybrid.py`
