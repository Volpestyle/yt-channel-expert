from __future__ import annotations
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Protocol, Sequence

from ...types import TranscriptSegment
from ..transcripts import load_transcript_file

class TranscriptFetchError(RuntimeError):
    pass

class Transcriber(Protocol):
    def transcribe(self, audio_path: Path, video_id: str) -> List[TranscriptSegment]:
        raise NotImplementedError

@dataclass
class TranscriptFetchConfig:
    languages: Optional[Sequence[str]] = None
    allow_auto: bool = True
    allow_ytdlp: bool = True

class WhisperTranscriber:
    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._backend: Optional[str] = None
        self._model = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore
            self._backend = "faster_whisper"
            self._model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
            return
        except ImportError:
            pass

        try:
            import whisper  # type: ignore
            self._backend = "openai_whisper"
            self._model = whisper.load_model(self.model_name)
            return
        except ImportError as exc:
            raise ImportError(
                "WhisperTranscriber requires faster-whisper or openai-whisper"
            ) from exc

    def transcribe(self, audio_path: Path, video_id: str) -> List[TranscriptSegment]:
        if self._backend == "faster_whisper":
            return self._transcribe_faster_whisper(audio_path, video_id)
        return self._transcribe_openai_whisper(audio_path, video_id)

    def _transcribe_faster_whisper(self, audio_path: Path, video_id: str) -> List[TranscriptSegment]:
        segments, _info = self._model.transcribe(str(audio_path), language=self.language)
        results: List[TranscriptSegment] = []
        for seg in segments:
            text = str(seg.text).strip()
            if not text:
                continue
            results.append(
                TranscriptSegment(
                    video_id=video_id,
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    text=text,
                )
            )
        return results

    def _transcribe_openai_whisper(self, audio_path: Path, video_id: str) -> List[TranscriptSegment]:
        result = self._model.transcribe(str(audio_path), language=self.language)
        segments = result.get("segments", [])
        results: List[TranscriptSegment] = []
        for seg in segments:
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            results.append(
                TranscriptSegment(
                    video_id=video_id,
                    start_ms=int(float(seg.get("start", 0)) * 1000),
                    end_ms=int(float(seg.get("end", 0)) * 1000),
                    text=text,
                )
            )
        return results

def fetch_transcript_segments(
    video_id: str,
    url: Optional[str] = None,
    config: Optional[TranscriptFetchConfig] = None,
    transcriber: Optional[Transcriber] = None,
) -> List[TranscriptSegment]:
    cfg = config or TranscriptFetchConfig()
    errors: List[str] = []

    try:
        return _fetch_with_youtube_transcript_api(video_id, cfg.languages)
    except Exception as exc:
        errors.append(f"youtube-transcript-api: {exc}")

    if cfg.allow_ytdlp:
        try:
            return _fetch_with_ytdlp_subtitles(video_id, url, cfg.languages, cfg.allow_auto)
        except Exception as exc:
            errors.append(f"yt-dlp subtitles: {exc}")

    if transcriber is not None:
        try:
            return _fetch_with_asr(video_id, url, transcriber)
        except Exception as exc:
            errors.append(f"asr: {exc}")

    raise TranscriptFetchError("Transcript fetch failed: " + " | ".join(errors))

def fetch_and_write_transcript(
    output_dir: Path,
    video_id: str,
    url: Optional[str] = None,
    config: Optional[TranscriptFetchConfig] = None,
    transcriber: Optional[Transcriber] = None,
) -> Path:
    segments = fetch_transcript_segments(video_id, url=url, config=config, transcriber=transcriber)
    return write_transcript_json(output_dir, video_id, segments)

def write_transcript_json(
    output_dir: Path,
    video_id: str,
    segments: Iterable[TranscriptSegment],
) -> Path:
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    path = transcripts_dir / f"{video_id}.json"
    rows = [
        {
            "start_ms": seg.start_ms,
            "end_ms": seg.end_ms,
            "text": seg.text,
            **({"speaker": seg.speaker} if seg.speaker else {}),
        }
        for seg in segments
    ]
    path.write_text(_dump_json(rows), encoding="utf-8")
    return path

def _dump_json(data: object) -> str:
    import json
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n"

def _default_languages(languages: Optional[Sequence[str]]) -> List[str]:
    if not languages:
        return ["en"]
    return list(languages)

def _fetch_with_youtube_transcript_api(
    video_id: str,
    languages: Optional[Sequence[str]] = None,
) -> List[TranscriptSegment]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError as exc:
        raise ImportError("youtube-transcript-api is required for caption fetch") from exc

    langs = _default_languages(languages)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
    return _segments_from_transcript_api(video_id, transcript)

def _segments_from_transcript_api(video_id: str, rows: Iterable[dict]) -> List[TranscriptSegment]:
    segments: List[TranscriptSegment] = []
    for row in rows:
        text = str(row.get("text", "")).strip()
        if not text:
            continue
        start = float(row.get("start", 0))
        duration = float(row.get("duration", 0))
        segments.append(
            TranscriptSegment(
                video_id=video_id,
                start_ms=int(start * 1000),
                end_ms=int((start + duration) * 1000),
                text=text,
            )
        )
    return segments

def _fetch_with_ytdlp_subtitles(
    video_id: str,
    url: Optional[str],
    languages: Optional[Sequence[str]],
    allow_auto: bool,
) -> List[TranscriptSegment]:
    yt_dlp = _require_yt_dlp()
    target_url = url or f"https://www.youtube.com/watch?v={video_id}"
    langs = _default_languages(languages)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        opts = {
            "skip_download": True,
            "quiet": True,
            "writesubtitles": True,
            "writeautomaticsub": bool(allow_auto),
            "subtitleslangs": langs,
            "subtitlesformat": "vtt",
            "outtmpl": str(tmp_path / "%(id)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([target_url])

        subtitle_path = _find_subtitle_file(tmp_path)
        if subtitle_path is None:
            raise TranscriptFetchError("No subtitle file downloaded")
        return load_transcript_file(subtitle_path, video_id)

def _fetch_with_asr(
    video_id: str,
    url: Optional[str],
    transcriber: Transcriber,
) -> List[TranscriptSegment]:
    yt_dlp = _require_yt_dlp()
    target_url = url or f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        opts = {
            "quiet": True,
            "format": "bestaudio/best",
            "outtmpl": str(tmp_path / "%(id)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target_url, download=True)

        info = _normalize_video_info(info)
        audio_path = tmp_path / f"{info['id']}.{info['ext']}"
        if not audio_path.exists():
            raise TranscriptFetchError("Audio download failed")
        return transcriber.transcribe(audio_path, video_id)

def _normalize_video_info(info: dict) -> dict:
    if "entries" in info and info["entries"]:
        return info["entries"][0]
    return info

def _find_subtitle_file(tmp_path: Path) -> Optional[Path]:
    for ext in ("vtt", "srt", "json"):
        matches = sorted(tmp_path.glob(f"*.{ext}"))
        if matches:
            return matches[0]
    return None

def _require_yt_dlp():
    try:
        import yt_dlp  # type: ignore
        return yt_dlp
    except ImportError as exc:
        raise ImportError("yt-dlp is required for subtitle/audio download") from exc
