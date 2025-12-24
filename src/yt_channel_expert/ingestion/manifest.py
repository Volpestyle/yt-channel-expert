from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple
from ..types import Channel, Video

def load_manifest(input_dir: Path) -> Tuple[Channel, List[Video]]:
    channel_path = input_dir / "channel.json"
    videos_path = input_dir / "videos.json"
    channel_data = json.loads(channel_path.read_text(encoding="utf-8"))
    videos_data = json.loads(videos_path.read_text(encoding="utf-8"))

    channel = Channel(
        channel_id=channel_data["channel_id"],
        title=channel_data.get("title", ""),
        description=channel_data.get("description", ""),
        source=channel_data.get("source", "local_manifest"),
    )
    videos: List[Video] = []
    for v in videos_data:
        videos.append(Video(
            video_id=v["video_id"],
            channel_id=channel.channel_id,
            title=v.get("title", ""),
            description=v.get("description", ""),
            published_at=v.get("published_at", ""),
            duration_sec=int(v.get("duration_sec", 0)),
            url=v.get("url", ""),
        ))
    return channel, videos
