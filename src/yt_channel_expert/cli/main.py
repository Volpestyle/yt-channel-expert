from __future__ import annotations
from pathlib import Path
import json
import typer
from rich.console import Console
from rich.pretty import Pretty

from ..config import PackConfig
from ..pack.pack_builder import PackBuilder
from ..rag.answerer import Answerer
from ..rag.prompts import build_messages
from ..pack.pack_reader import PackReader
from ..embeddings.factory import make_embedder
from ..llm.factory import make_llm
from ..rag.retriever import PackRetriever

app = typer.Typer(no_args_is_help=True)
console = Console()

pack_app = typer.Typer(no_args_is_help=True)
app.add_typer(pack_app, name="pack")

def _load_cfg(config: Path | None) -> PackConfig:
    if config is None:
        return PackConfig()
    return PackConfig.model_validate_json(config.read_text(encoding="utf-8"))

@pack_app.command("build")
def pack_build(
    input: Path = typer.Option(..., "--input", "-i", help="Input folder with channel.json, videos.json, transcripts/"),
    out: Path = typer.Option(..., "--out", "-o", help="Output .pack file"),
    config: Path = typer.Option(None, "--config", "-c", help="Optional JSON config file (PackConfig as JSON)"),
):
    cfg = _load_cfg(config)
    builder = PackBuilder(cfg)
    out_path = builder.build_from_folder(input, out)
    console.print(f"[green]Wrote pack:[/green] {out_path}")

@pack_app.command("info")
def pack_info(pack: Path = typer.Option(..., "--pack", "-p")):
    import zipfile
    with zipfile.ZipFile(pack, "r") as z:
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
    console.print(Pretty(manifest))

@pack_app.command("ask")
def pack_ask(
    pack: Path = typer.Option(..., "--pack", "-p"),
    question: str = typer.Option(..., "--question", "-q"),
    config: Path = typer.Option(None, "--config", "-c", help="Optional JSON config file (PackConfig as JSON)"),
    stream: bool = typer.Option(False, "--stream", help="Stream output if backend supports it"),
):
    cfg = _load_cfg(config)

    if not stream:
        ans = Answerer(cfg).answer(str(pack), question)
        console.print(ans.answer)
        console.print()
        console.print(f"citations_present={ans.citations_present}")
        console.print(Pretty(ans.debug))
        raise typer.Exit()

    # Streaming pipeline
    embedder = make_embedder(cfg.embedding)
    llm = make_llm(cfg.llm)

    with PackReader(pack) as pr:
        conn = pr.connect()
        manifest = pr.paths.manifest if pr.paths else {}
        channel_title = manifest.get("channel_title", "Unknown Channel")

        sec_emb, chunk_emb = pr.load_embeddings()
        bm25_docs = pr.load_bm25_docs()

        retriever = PackRetriever(conn, embedder, sec_emb, chunk_emb, bm25_docs=bm25_docs)
        ctx = retriever.retrieve(
            question,
            top_sections=cfg.retrieval.top_sections,
            top_chunks=cfg.retrieval.top_chunks,
            bm25_top_k=cfg.retrieval.bm25_top_k,
        )

        messages = build_messages(question, channel_title, ctx.section_summaries, ctx.chunks)
        response_format = {"type": "text"}

        for delta in llm.stream_generate(messages, response_format=response_format):
            console.print(delta, end="")

        console.print()
        console.print(Pretty({"sections": ctx.section_summaries, "chunks": len(ctx.chunks)}))
