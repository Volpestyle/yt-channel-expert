from __future__ import annotations
from typing import List, Protocol

from .models import ChannelInfo, VideoInfo

class YouTubeCatalog(Protocol):
    def get_channel(self, channel_ref: str) -> ChannelInfo:
        """Resolve a channel by URL or ID and return metadata."""
        raise NotImplementedError

    def list_videos(self, channel_id: str) -> List[VideoInfo]:
        """List videos for a channel, including published_at for sorting."""
        raise NotImplementedError

    def list_playlist_video_ids(self, playlist_id: str) -> List[str]:
        """Return video IDs in playlist order."""
        raise NotImplementedError
