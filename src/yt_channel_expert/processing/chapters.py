from __future__ import annotations
import re
from typing import List, Tuple

# Matches lines like:
# 00:00 Intro
# 1:02:03 Something
_CHAPTER = re.compile(r"^(?P<ts>(?:\d\d:)?\d\d:\d\d)\s+(?P<title>.+?)\s*$")

def parse_chapters_from_description(description: str) -> List[Tuple[int, str]]:
    """Return list of (start_ms, title) sorted by time."""
    chapters: List[Tuple[int, str]] = []
    for line in description.splitlines():
        m = _CHAPTER.match(line.strip())
        if not m:
            continue
        ts = m.group("ts")
        title = m.group("title").strip()
        parts = [int(p) for p in ts.split(":")]
        if len(parts) == 2:
            mm, ss = parts
            start_ms = (mm * 60 + ss) * 1000
        else:
            hh, mm, ss = parts
            start_ms = (hh * 3600 + mm * 60 + ss) * 1000
        chapters.append((start_ms, title))
    chapters.sort(key=lambda x: x[0])
    return chapters
