from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass(frozen=True)
class Channel:
    channel_id: str
    title: str
    description: str = ""
    source: str = "unknown"

@dataclass(frozen=True)
class Video:
    video_id: str
    channel_id: str
    title: str
    description: str = ""
    published_at: str = ""
    duration_sec: int = 0
    url: str = ""

@dataclass(frozen=True)
class TranscriptSegment:
    video_id: str
    start_ms: int
    end_ms: int
    text: str
    speaker: Optional[str] = None

@dataclass(frozen=True)
class MicroChunk:
    video_id: str
    start_ms: int
    end_ms: int
    text: str
    section_id: Optional[int] = None

@dataclass(frozen=True)
class Section:
    video_id: str
    start_ms: int
    end_ms: int
    title: str
    summary: str = ""

@dataclass(frozen=True)
class RetrievedChunk:
    video_id: str
    title: str
    url: str
    start_ms: int
    end_ms: int
    text: str
    score: float

def ms_to_timestamp(ms: int) -> str:
    # hh:mm:ss
    s = ms // 1000
    hh = s // 3600
    mm = (s % 3600) // 60
    ss = s % 60
    if hh > 0:
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    return f"{mm:02d}:{ss:02d}"
