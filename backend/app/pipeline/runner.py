"""Orchestration for the Phase 1 pipeline."""

import shutil
import tempfile
from pathlib import Path

from app.pipeline.extract import _fallback, extract_information
from app.pipeline.fetch import fetch_reel
from app.pipeline.normalize import normalize_instagram_url
from app.pipeline.ocr import extract_ocr
from app.pipeline.transcribe import transcribe_audio
from app.schemas import PipelineResult


def process_reel(
    url: str,
    thumbnail_dir: Path | str = Path("data/thumbnails"),
    whisper_model: str = "small",
) -> PipelineResult:
    """Process one reel while deleting all downloaded media in every outcome."""
    canonical_url, shortcode = normalize_instagram_url(url)
    errors: list[str] = []
    thumbnail_dir = Path(thumbnail_dir)
    temp_dir = Path(tempfile.mkdtemp(prefix="reelbrief-"))
    thumbnail_path = thumbnail_dir / f"{shortcode}.jpg"
    metadata: dict = {}
    try:
        try:
            metadata = fetch_reel(canonical_url, temp_dir, thumbnail_path)
        except Exception as exc:
            errors.append(f"fetch: {exc}")

        try:
            transcript, language = transcribe_audio(metadata.get("audio_path"), whisper_model)
        except Exception as exc:
            errors.append(f"transcription: {exc}")
            transcript, language = "", None

        try:
            ocr_text = extract_ocr(metadata.get("media_path"))
        except Exception as exc:
            errors.append(f"ocr: {exc}")
            ocr_text = ""

        try:
            extraction = extract_information(metadata.get("caption", ""), transcript, ocr_text)
        except Exception as exc:
            errors.append(f"extraction: {exc}")
            extraction = _fallback(metadata.get("caption", ""), transcript, ocr_text)

        return PipelineResult(
            shortcode=shortcode,
            url=canonical_url,
            caption=metadata.get("caption", ""),
            uploader=metadata.get("uploader"),
            transcript=transcript,
            ocr_text=ocr_text,
            language=language,
            extraction=extraction,
            errors=errors,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
