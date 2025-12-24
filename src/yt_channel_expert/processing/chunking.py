from __future__ import annotations
from typing import List
from ..types import TranscriptSegment, MicroChunk

def build_micro_chunks(
    segments: List[TranscriptSegment],
    chunk_sec: int = 45,
    overlap_sec: int = 15,
) -> List[MicroChunk]:
    if not segments:
        return []
    segs = sorted(segments, key=lambda s: s.start_ms)
    start_ms = segs[0].start_ms
    end_ms = segs[-1].end_ms

    step_ms = max(1, (chunk_sec - overlap_sec) * 1000)
    window_ms = chunk_sec * 1000

    chunks: List[MicroChunk] = []
    t = start_ms
    while t < end_ms:
        w_start = t
        w_end = t + window_ms
        buf = []
        for s in segs:
            if s.end_ms <= w_start:
                continue
            if s.start_ms >= w_end:
                break
            buf.append(s.text)
        text = " ".join(buf).strip()
        if text:
            chunks.append(MicroChunk(video_id=segs[0].video_id, start_ms=w_start, end_ms=min(w_end, end_ms), text=text))
        t += step_ms
    return chunks
