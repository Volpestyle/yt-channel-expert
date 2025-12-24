from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Sequence

from .catalog import YouTubeCatalog
from .models import ChannelInfo, VideoInfo
from .selection import SelectionSpec, select_videos

def write_manifest(output_dir: Path, channel: ChannelInfo, videos: Sequence[VideoInfo]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    channel_data = {
        "channel_id": channel.channel_id,
        "title": channel.title,
        "description": channel.description,
        "source": channel.source,
    }
    if channel.url:
        channel_data["url"] = channel.url

    videos_data = [
        {
            "video_id": v.video_id,
            "title": v.title,
            "description": v.description,
            "published_at": v.published_at,
            "duration_sec": v.duration_sec,
            "url": v.url,
        }
        for v in videos
    ]

    (output_dir / "channel.json").write_text(
        json.dumps(channel_data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "videos.json").write_text(
        json.dumps(videos_data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

def build_manifest_from_catalog(
    catalog: YouTubeCatalog,
    channel_ref: str,
    output_dir: Path,
    selection: Optional[SelectionSpec] = None,
) -> None:
    spec = selection or SelectionSpec()
    channel = catalog.get_channel(channel_ref)
    videos = catalog.list_videos(channel.channel_id)

    if spec.mode == "playlist" and spec.playlist_video_ids is None:
        if not spec.playlist_id:
            raise ValueError("playlist_id required when selection mode is playlist")
        playlist_video_ids = catalog.list_playlist_video_ids(spec.playlist_id)
        spec = SelectionSpec(
            mode=spec.mode,
            limit=spec.limit,
            playlist_id=spec.playlist_id,
            playlist_video_ids=playlist_video_ids,
            video_ids=spec.video_ids,
        )

    selected = select_videos(videos, spec)
    write_manifest(output_dir, channel, selected)
