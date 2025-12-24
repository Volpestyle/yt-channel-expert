from __future__ import annotations
from dataclasses import replace
from typing import List, Optional, Tuple
import numpy as np
from ..types import MicroChunk, Section

def build_sections_from_chapters(
    video_id: str,
    chapters: List[Tuple[int, str]],
    video_end_ms: int,
) -> List[Section]:
    if not chapters:
        return []
    sections: List[Section] = []
    for idx, (start_ms, title) in enumerate(chapters):
        end_ms = video_end_ms
        if idx + 1 < len(chapters):
            end_ms = chapters[idx + 1][0]
        if end_ms <= start_ms:
            continue
        sections.append(Section(video_id=video_id, start_ms=start_ms, end_ms=end_ms, title=title))
    return sections

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)

def auto_chapter_sections(
    video_id: str,
    chunks: List[MicroChunk],
    chunk_embeddings: np.ndarray,
    target_section_sec: int = 7 * 60,
    max_section_sec: int = 12 * 60,
    boundary_percentile: float = 92.0,
) -> List[Section]:
    """Detect topic shifts using embedding distance spikes.

    Args:
      chunk_embeddings: shape (len(chunks), dim)
    """
    if not chunks:
        return []
    if len(chunks) != chunk_embeddings.shape[0]:
        raise ValueError("chunks and embeddings length mismatch")

    # Distance between consecutive embeddings
    dists: List[float] = [0.0]
    for i in range(1, len(chunks)):
        sim = _cosine(chunk_embeddings[i], chunk_embeddings[i - 1])
        dists.append(1.0 - sim)
    thresh = float(np.percentile(np.array(dists[1:]), boundary_percentile)) if len(dists) > 2 else 1.0

    boundaries = [0]
    for i in range(1, len(chunks)):
        if dists[i] >= thresh:
            boundaries.append(i)
    boundaries.append(len(chunks))
    boundaries = sorted(set(boundaries))

    # Build sections with time constraints
    target_ms = target_section_sec * 1000
    max_ms = max_section_sec * 1000
    sections: List[Section] = []

    cur_start_idx = 0
    while cur_start_idx < len(chunks):
        cur_start_ms = chunks[cur_start_idx].start_ms
        # propose an end idx by accumulating time up to target, but allow boundary alignment
        end_idx = cur_start_idx + 1
        while end_idx < len(chunks) and chunks[end_idx - 1].end_ms - cur_start_ms < target_ms:
            end_idx += 1
        # snap end_idx to the next boundary at or after end_idx (if any)
        snap = None
        for b in boundaries:
            if b >= end_idx:
                snap = b
                break
        if snap is not None and snap > cur_start_idx:
            end_idx = snap
        # enforce max
        while end_idx < len(chunks) and chunks[end_idx - 1].end_ms - cur_start_ms < max_ms:
            # if already at boundary, stop; else extend a bit
            if end_idx in boundaries:
                break
            end_idx += 1
        end_idx = min(end_idx, len(chunks))

        sec_end_ms = chunks[end_idx - 1].end_ms
        title = f"Section {len(sections)+1}"
        sections.append(Section(video_id=video_id, start_ms=cur_start_ms, end_ms=sec_end_ms, title=title))
        cur_start_idx = end_idx

    return sections

def assign_chunks_to_sections(chunks: List[MicroChunk], sections: List[Section]) -> List[MicroChunk]:
    if not sections:
        return chunks
    out: List[MicroChunk] = []
    sidx = 0
    for ch in chunks:
        while sidx + 1 < len(sections) and ch.start_ms >= sections[sidx].end_ms:
            sidx += 1
        sec_id = sidx
        out.append(replace(ch, section_id=sec_id))
    return out
