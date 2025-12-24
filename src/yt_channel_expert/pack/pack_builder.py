from __future__ import annotations
import json
import os
import sqlite3
import tempfile
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from tqdm import tqdm

from ..config import PackConfig
from ..types import Channel, Video, TranscriptSegment, MicroChunk, Section
from ..ingestion.manifest import load_manifest
from ..ingestion.transcripts import load_transcript_file
from ..processing.normalize import normalize_segments
from ..processing.chapters import parse_chapters_from_description
from ..processing.chunking import build_micro_chunks
from ..processing.sections import (
    build_sections_from_chapters,
    auto_chapter_sections,
    assign_chunks_to_sections,
)
from ..embeddings.factory import make_embedder
from ..index.vector_index import BruteForceIndex
from ..index.bm25 import BM25
from .schema import create_schema, SCHEMA_VERSION

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

class PackBuilder:
    def __init__(self, cfg: PackConfig) -> None:
        self.cfg = cfg
        self.embedder = make_embedder(cfg.embedding)

    def build_from_folder(self, input_dir: Path, out_pack_path: Path) -> Path:
        channel, videos = load_manifest(input_dir)
        transcripts_dir = input_dir / "transcripts"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "pack.sqlite"
            vectors_dir = tmp_path / "vectors"
            vectors_dir.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path))
            create_schema(conn)
            self._insert_channel(conn, channel)
            self._insert_videos(conn, videos)

            # Collect text items for embeddings
            all_chunk_texts: List[str] = []
            chunk_rows: List[Tuple[MicroChunk, Video]] = []
            all_section_texts: List[str] = []
            section_rows: List[Tuple[Section, Video]] = []

            for v in tqdm(videos, desc="Processing videos"):
                tpath = self._find_transcript(transcripts_dir, v.video_id)
                segments: List[TranscriptSegment] = []
                if tpath and tpath.exists():
                    segments = load_transcript_file(tpath, v.video_id)
                    segments = normalize_segments(segments)
                    self._insert_segments(conn, v.video_id, segments)

                # Skip if no transcript
                if not segments:
                    continue

                # Build micro-chunks
                chunks = build_micro_chunks(
                    segments,
                    chunk_sec=self.cfg.chunking.micro_chunk_sec,
                    overlap_sec=self.cfg.chunking.micro_overlap_sec,
                )

                # Build sections from chapters or auto
                chapters = parse_chapters_from_description(v.description)
                video_end_ms = max(s.end_ms for s in segments)
                sections: List[Section] = []
                if chapters:
                    sections = build_sections_from_chapters(v.video_id, chapters, video_end_ms)
                else:
                    # Auto-chapter requires embeddings; we use hash embedder here too (works but not semantic).
                    chunk_emb = self.embedder.embed_texts([c.text for c in chunks])
                    sections = auto_chapter_sections(
                        video_id=v.video_id,
                        chunks=chunks,
                        chunk_embeddings=chunk_emb,
                        target_section_sec=self.cfg.chunking.target_section_sec,
                        max_section_sec=self.cfg.chunking.max_section_sec,
                    )

                sec_ids = self._insert_sections(conn, v.video_id, sections)
                # Assign chunks to sections by index order (sec_ids align with insertion order)
                chunks = assign_chunks_to_sections(chunks, sections)
                self._insert_chunks(conn, v.video_id, chunks, sec_ids)

                # Collect for embedding matrices
                for s in sections:
                    all_section_texts.append(f"{v.title}\n{s.title}\n{s.summary or ''}")
                    section_rows.append((s, v))
                for c in chunks:
                    all_chunk_texts.append(c.text)
                    chunk_rows.append((c, v))

            # Build embeddings and indices
            if all_section_texts:
                section_emb = self.embedder.embed_texts(all_section_texts)
                np.save(vectors_dir / "section_embeddings.npy", section_emb)
            if all_chunk_texts:
                chunk_emb = self.embedder.embed_texts(all_chunk_texts)
                np.save(vectors_dir / "chunk_embeddings.npy", chunk_emb)

            # Optional BM25 corpora
            bm25 = BM25()
            if all_chunk_texts and self.cfg.retrieval.use_bm25:
                bm25.add_documents(all_chunk_texts)
                # Persist BM25 tokens minimally by storing docs as joined tokens (toy)
                # Production: store DF + doc lens.
                with open(vectors_dir / "bm25_docs.json", "w", encoding="utf-8") as f:
                    json.dump(all_chunk_texts, f)

            # Write manifest
            manifest = {
                "pack_version": 1,
                "schema_version": SCHEMA_VERSION,
                "created_at": _now_iso(),
                "channel_id": channel.channel_id,
                "channel_title": channel.title,
                "embedding_dim": int(self.embedder.dim),
                "embedding_model_id": self.cfg.embedding.model_name,
                "video_count": len(videos),
                "note": "This is a spec scaffold. Replace hash embeddings + toy bm25 persistence for production.",
            }
            (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            # Bundle
            out_pack_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(out_pack_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.write(tmp_path / "manifest.json", arcname="manifest.json")
                z.write(db_path, arcname="pack.sqlite")
                for p in vectors_dir.rglob("*"):
                    z.write(p, arcname=str(p.relative_to(tmp_path)))

        return out_pack_path

    def _find_transcript(self, transcripts_dir: Path, video_id: str) -> Path | None:
        for ext in (".srt", ".vtt", ".json"):
            p = transcripts_dir / f"{video_id}{ext}"
            if p.exists():
                return p
        return None

    def _insert_channel(self, conn: sqlite3.Connection, ch: Channel) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO channel(channel_id,title,description,source,created_at,last_sync_at) VALUES (?,?,?,?,?,?)",
            (ch.channel_id, ch.title, ch.description, ch.source, _now_iso(), _now_iso()),
        )
        conn.commit()

    def _insert_videos(self, conn: sqlite3.Connection, videos: List[Video]) -> None:
        for v in videos:
            conn.execute(
                "INSERT OR REPLACE INTO video(video_id,channel_id,title,description,published_at,duration_sec,url) VALUES (?,?,?,?,?,?,?)",
                (v.video_id, v.channel_id, v.title, v.description, v.published_at, v.duration_sec, v.url),
            )
        conn.commit()

    def _insert_segments(self, conn: sqlite3.Connection, video_id: str, segments: List[TranscriptSegment]) -> None:
        conn.executemany(
            "INSERT INTO transcript_segment(video_id,start_ms,end_ms,text,speaker) VALUES (?,?,?,?,?)",
            [(s.video_id, s.start_ms, s.end_ms, s.text, s.speaker) for s in segments],
        )
        conn.commit()

    def _insert_sections(self, conn: sqlite3.Connection, video_id: str, sections: List[Section]) -> List[int]:
        ids: List[int] = []
        for s in sections:
            cur = conn.execute(
                "INSERT INTO section(video_id,start_ms,end_ms,title,summary) VALUES (?,?,?,?,?)",
                (s.video_id, s.start_ms, s.end_ms, s.title, s.summary),
            )
            ids.append(int(cur.lastrowid))
        conn.commit()
        return ids

    def _insert_chunks(self, conn: sqlite3.Connection, video_id: str, chunks: List[MicroChunk], section_ids: List[int]) -> None:
        rows = []
        for c in chunks:
            sec_db_id = None
            if c.section_id is not None and 0 <= c.section_id < len(section_ids):
                sec_db_id = section_ids[c.section_id]
            rows.append((c.video_id, sec_db_id, c.start_ms, c.end_ms, c.text))
        conn.executemany(
            "INSERT INTO micro_chunk(video_id,section_id,start_ms,end_ms,text) VALUES (?,?,?,?,?)",
            rows,
        )
        conn.commit()
