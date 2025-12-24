# Consuming applications (AWS/serverless patterns)

This repo’s core runtime is pure Python: read a `.pack`, retrieve sections/chunks, assemble a prompt, call an LLM, and return citations. That makes it compatible with AWS serverless, as long as you handle the pack’s storage and extraction.

## What the runtime expects

- A `.pack` file (zip) containing:
  - `pack.sqlite` (metadata + transcripts + summaries)
  - `vectors/` (embedding matrices / index artifacts)
  - `manifest.json`
- The app loads the pack, extracts it locally, then opens SQLite and memory-maps vectors.
- The retriever embeds each user question at runtime (cheap if using the hash embedder).

## Recommended AWS shapes

### Option A: Lambda + S3 (single-tenant)

Best for one channel or a small number of packs.

- Store `.pack` in S3.
- Lambda downloads the pack to `/tmp` on cold start and reuses it on warm invocations.
- Use `llmhub` backend to call a managed LLM (Bedrock, OpenAI, etc.).

Notes:
- `/tmp` has size limits; keep packs small.
- Cold start cost includes unzip + loading vectors.
- Lambda memory can scale up, but large packs may exceed memory or storage limits.

### Option B: Lambda + EFS (multi-tenant)

Best for many packs or large packs.

- Mount EFS and store unpacked pack folders per channel.
- Lambda opens SQLite from EFS and reads vector files directly.
- Avoids repeated unzip and reduces cold-start work.

### Option C: Fargate/ECS (performance-first)

Best for large packs or strict latency.

- Keep packs local on container disk.
- Use HNSW index and higher RAM.
- Lower tail latency vs Lambda.

## Minimal Lambda flow (single-tenant)

1. On cold start, download pack from S3 to `/tmp/pack.pack`.
2. If not extracted, unzip to `/tmp/pack/` and reuse across warm invocations.
3. For each request:
   - open SQLite
   - load vectors
   - retrieve + assemble prompt
   - call LLM
   - return citations

Pseudo-code sketch:

```python
PACK_S3_URI = os.environ["PACK_S3_URI"]
LOCAL_PACK = "/tmp/pack.pack"
LOCAL_DIR = "/tmp/pack"

if not os.path.exists(LOCAL_DIR):
    download_from_s3(PACK_S3_URI, LOCAL_PACK)
    unzip(LOCAL_PACK, LOCAL_DIR)

# PackReader extracts to a temp dir each call. For Lambda, consider
# a small wrapper that points to a pre-extracted folder to avoid unzip
# on every request.
with PackReader(Path(LOCAL_PACK)) as pr:
    ... answer(question) ...
```

## Multi-tenant pattern (many channels)

- Store packs in S3 under `packs/{channel_id}.pack`.
- Cache a small LRU of packs in `/tmp` (or keep unpacked packs on EFS).
- Use a request parameter to select the pack.

Cache strategy:
- If pack not present in cache, download + unzip.
- Evict oldest pack if `/tmp` storage gets tight.

## LLM + embeddings guidance

- Keep embeddings lightweight in Lambda:
  - default `hash` embedder (fast, no extra deps)
  - avoid `sentence_transformer` unless you bundle the model into an image
- Prefer `llmhub` backend and point it to a managed LLM endpoint.

## Operational checklists

- Ensure `pack.sqlite` exists in the pack (required).
- Make sure the pack includes the vector files the retriever expects.
- For HNSW indexes, ship `hnswlib` via Lambda layer or container image.
- Use CloudWatch logs for retrieval/LLM latency visibility.

## Lambda size limits (practical)

Lambda has both memory and ephemeral storage constraints. Large packs can hit either limit:

- **Memory**: scales with your function size (up to 10 GB). The pack, vectors, and Python process must all fit.
- **Ephemeral storage (`/tmp`)**: defaults to 512 MB and can be increased up to 10 GB.

If your unpacked `.pack` exceeds `/tmp` or you see high memory pressure, use EFS or Fargate.

## Pack scope (full channel vs playlist/series)

You are not required to ingest an entire channel. The pack builder accepts a local input folder with a `videos.json` manifest plus matching transcript files, so you can build packs for:

- a single playlist or series,
- a date range,
- or any curated subset of videos.

Just generate the manifest and transcripts for the subset you want and build a pack from that folder.

See also: `docs/13_llmhub_integration.md` for wiring managed LLMs.
