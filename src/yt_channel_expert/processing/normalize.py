from __future__ import annotations
import re
from typing import List
from ..types import TranscriptSegment

_WS = re.compile(r"\s+")

def normalize_segments(segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
    out: List[TranscriptSegment] = []
    for s in segments:
        txt = _WS.sub(" ", s.text).strip()
        if not txt:
            continue
        out.append(TranscriptSegment(
            video_id=s.video_id,
            start_ms=s.start_ms,
            end_ms=s.end_ms,
            text=txt,
            speaker=s.speaker,
        ))
    return out
