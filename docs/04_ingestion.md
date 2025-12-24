# Ingestion

This repo is intentionally **source-agnostic** about transcripts:

- If you **own/manage** the channel, you can implement an OAuth caption downloader.
- Otherwise, use **manual transcript import** (VTT/SRT/JSON) and/or **local transcription** from audio you are authorized to use.

The pack builder expects a local folder with:
- `videos.json` manifest (video_id, title, url, published_at, duration)
- `transcripts/VIDEO_ID.(vtt|srt|json)` files (optional per video)

See `examples/demo_channel/`.

## Playlist or series-only packs

You can build a pack for a subset of a channel (playlist/series/date range) by generating a smaller `videos.json` that only includes those videos, plus the matching transcript files.

Example `videos.json` (playlist-only):

```json
{
  "channel": {
    "channel_id": "UC123",
    "title": "Example Channel",
    "source": "playlist:PLabc123"
  },
  "videos": [
    {
      "video_id": "vid_001",
      "title": "Episode 1",
      "url": "https://youtube.com/watch?v=vid_001",
      "published_at": "2023-06-01T00:00:00Z",
      "duration_sec": 1800
    },
    {
      "video_id": "vid_002",
      "title": "Episode 2",
      "url": "https://youtube.com/watch?v=vid_002",
      "published_at": "2023-06-08T00:00:00Z",
      "duration_sec": 1920
    }
  ]
}
```

Then place transcripts in `transcripts/vid_001.vtt`, `transcripts/vid_002.vtt`, etc., and run the pack build on that folder.

## Ingestion flow

![Ingestion flow](diagrams/exports/ingestion-flow.png)

## Chapters

Chapters can come from:
- explicit timestamps in the video description (if present),
- or **auto-chaptering** based on topic shifts (see `docs/05_chunking_and_sections.md`).

Next: `docs/05_chunking_and_sections.md`.
