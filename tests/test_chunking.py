from yt_channel_expert.types import TranscriptSegment
from yt_channel_expert.processing.chunking import build_micro_chunks

def test_micro_chunking():
    segs = [
        TranscriptSegment(video_id="v", start_ms=0, end_ms=10_000, text="a"),
        TranscriptSegment(video_id="v", start_ms=10_000, end_ms=20_000, text="b"),
        TranscriptSegment(video_id="v", start_ms=20_000, end_ms=30_000, text="c"),
    ]
    chunks = build_micro_chunks(segs, chunk_sec=15, overlap_sec=5)
    assert len(chunks) >= 2
    assert chunks[0].start_ms == 0
