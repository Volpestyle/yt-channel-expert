from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Optional
from ..types import TranscriptSegment

_SRT_TS = re.compile(
    r"(\d\d):(\d\d):(\d\d),(\d\d\d)\s*-->\s*(\d\d):(\d\d):(\d\d),(\d\d\d)"
)

def _ts_to_ms(hh: str, mm: str, ss: str, ms: str) -> int:
    return (int(hh) * 3600 + int(mm) * 60 + int(ss)) * 1000 + int(ms)

def parse_srt(video_id: str, content: str, speaker: Optional[str] = None) -> List[TranscriptSegment]:
    lines = [ln.rstrip("\n") for ln in content.splitlines()]
    segments: List[TranscriptSegment] = []
    i = 0
    while i < len(lines):
        # skip index line if present
        if lines[i].strip().isdigit():
            i += 1
        if i >= len(lines):
            break
        m = _SRT_TS.match(lines[i].strip())
        if not m:
            i += 1
            continue
        start_ms = _ts_to_ms(m.group(1), m.group(2), m.group(3), m.group(4))
        end_ms = _ts_to_ms(m.group(5), m.group(6), m.group(7), m.group(8))
        i += 1
        buf = []
        while i < len(lines) and lines[i].strip() != "":
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf).strip()
        if text:
            segments.append(TranscriptSegment(video_id=video_id, start_ms=start_ms, end_ms=end_ms, text=text, speaker=speaker))
        # consume blank line
        while i < len(lines) and lines[i].strip() == "":
            i += 1
    return segments

def parse_json_segments(video_id: str, content: str) -> List[TranscriptSegment]:
    data = json.loads(content)
    segments: List[TranscriptSegment] = []
    for row in data:
        segments.append(
            TranscriptSegment(
                video_id=video_id,
                start_ms=int(row["start_ms"]),
                end_ms=int(row["end_ms"]),
                text=str(row["text"]),
                speaker=row.get("speaker"),
            )
        )
    return segments

def load_transcript_file(path: Path, video_id: str) -> List[TranscriptSegment]:
    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".srt":
        return parse_srt(video_id, content)
    if suffix == ".json":
        return parse_json_segments(video_id, content)
    if suffix == ".vtt":
        # Minimal VTT support: strip WEBVTT header and reuse SRT time parser by converting '.' to ','
        content2 = content.replace("WEBVTT", "").strip()
        content2 = content2.replace(".", ",")
        return parse_srt(video_id, content2)
    raise ValueError(f"Unsupported transcript format: {suffix}")
