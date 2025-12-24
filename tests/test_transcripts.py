from yt_channel_expert.ingestion.transcripts import parse_srt

def test_parse_srt_basic():
    srt = """1
00:00:00,000 --> 00:00:01,000
Hello world
"""
    segs = parse_srt("vid", srt)
    assert len(segs) == 1
    assert segs[0].start_ms == 0
    assert segs[0].end_ms == 1000
    assert "Hello" in segs[0].text
