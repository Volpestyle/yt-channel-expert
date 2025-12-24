# Overview

## What this is

A **local-first expert system** for a specific YouTube channel.

It does two big jobs:

1. **Build** a portable, offline **Channel Pack** from a channel’s videos.
2. **Answer** questions using **Retrieval-Augmented Generation (RAG)** with **timestamped citations**.

This repo focuses on **Python backend logic** (pack building + retrieval + orchestration).
A future iOS app can reuse the same **pack format** and implement the same retrieval logic in Swift.

## Design principles

- **Grounded answers**: every non-trivial claim must cite video + timestamp span.
- **Long video native**: supports 1–2 hour transcripts without dumping them into the LLM context.
- **Local-first**: after ingestion, Q&A can be fully offline.
- **Pluggable backends**: embeddings and LLM runtime are interfaces.

## Key concepts

- **Micro-chunks**: ~45 seconds transcript windows (overlapping) → used for precise retrieval + citations.
- **Sections**: 5–10 minute groupings of micro-chunks → used for “where in the episode” structure.
- **Episode summary**: map-reduce summarization over sections → used for broad questions.
- **Hybrid search**: vector similarity + keyword BM25 (optional) → robust retrieval.
- **Channel Pack**: a single portable file containing:
  - SQLite DB with metadata + transcripts + summaries
  - vector index (HNSW or brute-force matrix)
  - manifest + versioning

Next: `docs/02_architecture.md`.


See also: `docs/13_llmhub_integration.md` for llmhub-node integration.
See also: `docs/14_consuming_apps.md` for AWS/serverless consumption patterns.
