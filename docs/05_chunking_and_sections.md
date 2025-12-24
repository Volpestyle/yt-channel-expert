# Chunking and sections (long video support)

For 1–2 hour videos, we use **hierarchical segmentation**:

- **Micro-chunks**: ~45 seconds, overlap ~15 seconds.
- **Sections**: ~7 minutes target, max ~12 minutes, built from micro-chunks.
- **Episode summary**: map-reduce over sections.

## Why hierarchical?

Because you can’t put a 2-hour transcript into the context window of typical local models.
Instead:

1. retrieve the most relevant **sections** (coarse),
2. then retrieve the best **micro-chunks** inside those sections (fine).

## Micro-chunk algorithm

Inputs:
- `TranscriptSegment[]` with timestamps

Steps:
1. Iterate time in windows of `chunk_sec`, with overlap.
2. Collect segments that intersect the window.
3. Concatenate text, normalize whitespace.
4. Store chunk with `start_ms/end_ms`.

Default:
- `chunk_sec=45`, `overlap_sec=15`

## Section algorithm

### If creator provides chapters
Parse chapters from description, e.g.:

```
00:00 Intro
05:14 Topic A
...
```

Use those as sections.

### Otherwise: auto-chapter by topic shift
Use micro-chunk embeddings and detect change points.

Simplified approach:
- compute embedding `e_i` for each micro-chunk
- compute distance `d_i = 1 - cosine(e_i, e_{i-1})`
- mark boundaries where `d_i` is above a percentile threshold
- merge segments until you hit target section duration (7–10 min)

## Diagram: coarse-to-fine retrieval

![Coarse-to-fine retrieval](diagrams/exports/chunking-coarse-to-fine.png)

Implementation reference:
- `src/yt_channel_expert/processing/chunking.py`
- `src/yt_channel_expert/processing/sections.py`
