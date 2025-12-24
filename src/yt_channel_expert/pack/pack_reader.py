from __future__ import annotations
import json
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..errors import PackReadError

@dataclass
class PackPaths:
    root: Path
    db_path: Path
    vectors_dir: Path
    manifest: Dict

class PackReader:
    def __init__(self, pack_path: Path):
        self.pack_path = pack_path
        self._tmp: Optional[tempfile.TemporaryDirectory] = None
        self.paths: Optional[PackPaths] = None

    def __enter__(self) -> "PackReader":
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        with zipfile.ZipFile(self.pack_path, "r") as z:
            z.extractall(root)
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise PackReadError("manifest.json missing in pack")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        db_path = root / "pack.sqlite"
        if not db_path.exists():
            raise PackReadError("pack.sqlite missing in pack")
        vectors_dir = root / "vectors"
        self.paths = PackPaths(root=root, db_path=db_path, vectors_dir=vectors_dir, manifest=manifest)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
        self._tmp = None
        self.paths = None

    def connect(self) -> sqlite3.Connection:
        if not self.paths:
            raise PackReadError("PackReader not opened")
        return sqlite3.connect(str(self.paths.db_path))

    def load_embeddings(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if not self.paths:
            raise PackReadError("PackReader not opened")
        sec_path = self.paths.vectors_dir / "section_embeddings.npy"
        chunk_path = self.paths.vectors_dir / "chunk_embeddings.npy"
        sec = np.load(sec_path) if sec_path.exists() else None
        ch = np.load(chunk_path) if chunk_path.exists() else None
        return sec, ch

    def load_bm25_docs(self) -> Optional[List[str]]:
        if not self.paths:
            raise PackReadError("PackReader not opened")
        p = self.paths.vectors_dir / "bm25_docs.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
