from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from ..embeddings.embedder import Embedder
from ..index.vector_index import BruteForceIndex, HNSWIndex
from ..index.bm25 import BM25
from ..index.hybrid import HybridRetriever
from ..types import RetrievedChunk

@dataclass
class RetrievalContext:
    section_summaries: List[str]
    chunks: List[RetrievedChunk]

class PackRetriever:
    def __init__(
        self,
        conn: sqlite3.Connection,
        embedder: Embedder,
        section_embeddings: Optional[np.ndarray],
        chunk_embeddings: Optional[np.ndarray],
        bm25_docs: Optional[List[str]] = None,
        use_hnsw: bool = False,
    ) -> None:
        self.conn = conn
        self.embedder = embedder

        # Indices
        if section_embeddings is not None:
            self.section_index = BruteForceIndex()
            self.section_index.add(section_embeddings)
        else:
            self.section_index = None

        if chunk_embeddings is not None:
            self.chunk_index = BruteForceIndex()
            self.chunk_index.add(chunk_embeddings)
        else:
            self.chunk_index = None

        self.bm25: Optional[BM25] = None
        if bm25_docs is not None:
            bm = BM25()
            bm.add_documents(bm25_docs)
            self.bm25 = bm

    def retrieve(
        self,
        question: str,
        top_sections: int = 5,
        top_chunks: int = 10,
        bm25_top_k: int = 20,
    ) -> RetrievalContext:
        qvec = self.embedder.embed_texts([question])[0]

        section_ids: List[int] = []
        section_summaries: List[str] = []
        if self.section_index is not None:
            hits = self.section_index.search(qvec, top_k=top_sections)
            section_ids = [h.idx for h in hits]
            # Resolve section rows by rank order
            for sid in section_ids:
                row = self.conn.execute(
                    "SELECT title, start_ms, end_ms, video_id FROM section ORDER BY section_id LIMIT 1 OFFSET ?",
                    (sid,),
                ).fetchone()
                if row:
                    title, start_ms, end_ms, video_id = row
                    section_summaries.append(f"{video_id} {title} ({start_ms//1000}s–{end_ms//1000}s)")

        # Retrieve chunks, optionally restricted to selected sections (by section_id ordering)
        chunks: List[RetrievedChunk] = []
        if self.chunk_index is None:
            return RetrievalContext(section_summaries=section_summaries, chunks=chunks)

        # Hybrid merge between vector and BM25 over chunks
        hybrid = HybridRetriever(self.chunk_index, bm25=self.bm25, alpha=0.7)
        hits = hybrid.search(qvec, question, top_k=top_chunks, bm25_top_k=bm25_top_k)

        for h in hits:
            # Resolve chunk by rank using OFFSET (toy). Production: store chunk_id mapping to embedding row.
            row = self.conn.execute(
                """
                SELECT mc.video_id, v.title, v.url, mc.start_ms, mc.end_ms, mc.text
                FROM micro_chunk mc
                JOIN video v ON v.video_id = mc.video_id
                ORDER BY mc.chunk_id
                LIMIT 1 OFFSET ?
                """,
                (h.idx,),
            ).fetchone()
            if not row:
                continue
            video_id, title, url, start_ms, end_ms, text = row
            chunks.append(RetrievedChunk(
                video_id=video_id,
                title=title,
                url=url,
                start_ms=int(start_ms),
                end_ms=int(end_ms),
                text=text,
                score=float(h.score),
            ))

        return RetrievalContext(section_summaries=section_summaries, chunks=chunks)
