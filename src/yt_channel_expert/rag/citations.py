from __future__ import annotations
import re
from typing import List

_CITE = re.compile(r"\[[A-Za-z0-9_-]+\s*@\s*(?:\d\d:)?\d\d:\d\d-(?:\d\d:)?\d\d:\d\d\]")

def has_citations(text: str) -> bool:
    return _CITE.search(text) is not None

def count_citations(text: str) -> int:
    return len(_CITE.findall(text))
