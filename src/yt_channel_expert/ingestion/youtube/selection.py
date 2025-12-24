from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Literal

from .models import VideoInfo

@dataclass
class SelectionSpec:
    mode: Literal["latest", "playlist", "manual"] = "latest"
    limit: int = 20
    playlist_id: Optional[str] = None
    playlist_video_ids: Optional[List[str]] = None
    video_ids: Optional[List[str]] = None

def select_videos(videos: Sequence[VideoInfo], spec: SelectionSpec) -> List[VideoInfo]:
    if spec.mode == "latest":
        return _select_latest(videos, spec.limit)
    if spec.mode == "playlist":
        return _select_playlist(videos, spec)
    if spec.mode == "manual":
        return _select_manual(videos, spec.video_ids)
    raise ValueError(f"Unknown selection mode: {spec.mode}")

def _select_latest(videos: Sequence[VideoInfo], limit: int) -> List[VideoInfo]:
    if limit <= 0:
        return []
    return sorted(videos, key=lambda v: v.published_at or "", reverse=True)[:limit]

def _select_playlist(videos: Sequence[VideoInfo], spec: SelectionSpec) -> List[VideoInfo]:
    if spec.playlist_video_ids:
        video_map = {v.video_id: v for v in videos}
        return [video_map[vid] for vid in spec.playlist_video_ids if vid in video_map]
    if not spec.playlist_id:
        raise ValueError("playlist_id or playlist_video_ids is required for playlist selection")
    return [v for v in videos if spec.playlist_id in v.playlist_ids]

def _select_manual(videos: Sequence[VideoInfo], video_ids: Optional[List[str]]) -> List[VideoInfo]:
    if not video_ids:
        raise ValueError("video_ids is required for manual selection")
    video_map = {v.video_id: v for v in videos}
    return [video_map[vid] for vid in video_ids if vid in video_map]
