from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ChannelInfo:
    channel_id: str
    title: str
    description: str = ""
    source: str = "youtube"
    url: Optional[str] = None

@dataclass
class VideoInfo:
    video_id: str
    title: str
    url: str
    published_at: str
    duration_sec: int
    description: str = ""
    playlist_ids: List[str] = field(default_factory=list)
