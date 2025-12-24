from __future__ import annotations
from dataclasses import dataclass

from ..config import PackConfig
from ..embeddings.factory import make_embedder
from ..pack.pack_reader import PackReader
from ..llm.factory import make_llm
from .retriever import PackRetriever
from .prompts import build_messages
from .citations import has_citations

@dataclass
class AnswerResult:
    answer: str
    citations_present: bool
    debug: dict

class Answerer:
    def __init__(self, cfg: PackConfig):
        self.cfg = cfg
        self.embedder = make_embedder(cfg.embedding)
        self.llm = make_llm(cfg.llm)

    def answer(self, pack_path: str, question: str) -> AnswerResult:
        from pathlib import Path
        pack_path = str(pack_path)
        with PackReader(Path(pack_path)) as pr:
            conn = pr.connect()
            manifest = pr.paths.manifest if pr.paths else {}
            channel_title = manifest.get("channel_title", "Unknown Channel")

            sec_emb, chunk_emb = pr.load_embeddings()
            bm25_docs = pr.load_bm25_docs()

            retriever = PackRetriever(conn, self.embedder, sec_emb, chunk_emb, bm25_docs=bm25_docs)
            ctx = retriever.retrieve(
                question,
                top_sections=self.cfg.retrieval.top_sections,
                top_chunks=self.cfg.retrieval.top_chunks,
                bm25_top_k=self.cfg.retrieval.bm25_top_k,
            )

            messages = build_messages(question, channel_title, ctx.section_summaries, ctx.chunks)
            response_format = {"type": "text"}

            draft = self.llm.generate(messages, response_format=response_format)

            ok = has_citations(draft) if ctx.chunks else False
            if ctx.chunks and not ok:
                # Regenerate with stronger reminder
                messages2 = list(messages)
                messages2.append({
                    "role": "system",
                    "content": [{"type": "text", "text": "REMINDER: Every paragraph must include at least one citation like [video_id @ mm:ss-mm:ss]."}],
                })
                draft = self.llm.generate(messages2, response_format=response_format)
                ok = has_citations(draft)

            return AnswerResult(
                answer=draft,
                citations_present=ok,
                debug={
                    "sections": ctx.section_summaries,
                    "top_chunks": [
                        {"video_id": c.video_id, "ts": (c.start_ms, c.end_ms), "score": c.score}
                        for c in ctx.chunks
                    ],
                },
            )
