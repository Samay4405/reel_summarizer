"""Orchestration for the ReelBrief pipeline."""

import shutil
import tempfile
from pathlib import Path

from app.pipeline.extract import _fallback, extract_information
from app.pipeline.fetch import fetch_reel
from app.pipeline.normalize import normalize_instagram_url
from app.pipeline.ocr import extract_ocr
from app.pipeline.transcribe import transcribe_audio
from app.schemas import PipelineResult, ReelStatus


def process_reel(
    url: str,
    thumbnail_dir: Path | str = Path("data/thumbnails"),
    whisper_model: str | None = None,
    whisper_device: str | None = None,
    cookies_file: str | Path | None = None,
    caption: str | None = None,
    uploader: str | None = None,
) -> PipelineResult:
    """Process a single reel with guaranteed ephemeral disk cleanup.

    Distinguishes outcome statuses:
      - 'processed': full multimodal pipeline succeeded.
      - 'partial': media fetch failed, but caption was available for text analysis.
      - 'failed': media fetch failed and no usable caption was provided.
    """
    canonical_url, shortcode = normalize_instagram_url(url)
    errors: list[str] = []
    thumbnail_dir = Path(thumbnail_dir)
    temp_dir = Path(tempfile.mkdtemp(prefix="reelbrief-"))
    thumbnail_path = thumbnail_dir / f"{shortcode}.jpg"

    active_caption = caption or ""
    active_uploader = uploader
    transcript = ""
    ocr_text = ""
    language = None
    media_path = None

    try:
        try:
            fetch_kwargs = {}
            if cookies_file is not None:
                fetch_kwargs["cookies_file"] = cookies_file
            metadata = fetch_reel(
                canonical_url,
                temp_dir,
                thumbnail_path,
                **fetch_kwargs,
            )
            media_path = metadata.get("media_path")
            if metadata.get("caption"):
                active_caption = metadata["caption"]
            if metadata.get("uploader"):
                active_uploader = metadata["uploader"]
        except Exception as exc:
            errors.append(f"fetch: {exc}")

        # If media was downloaded, proceed with transcription and OCR
        if media_path and media_path.exists():
            try:
                transcript, language = transcribe_audio(
                    media_path,
                    model_name=whisper_model,
                    device=whisper_device,
                )
            except Exception as exc:
                errors.append(f"transcription: {exc}")
                transcript, language = "", None

            try:
                ocr_text = extract_ocr(media_path)
            except Exception as exc:
                errors.append(f"ocr: {exc}")
                ocr_text = ""

        # Determine status and extract structured insights
        status: ReelStatus
        has_content = bool(active_caption.strip() or transcript.strip() or ocr_text.strip())

        if media_path and media_path.exists():
            status = "processed"
            try:
                extraction = extract_information(active_caption, transcript, ocr_text)
            except Exception as exc:
                errors.append(f"extraction: {exc}")
                extraction = _fallback(active_caption, transcript, ocr_text)
        elif active_caption.strip():
            status = "partial"
            try:
                extraction = extract_information(active_caption, "", "")
            except Exception as exc:
                errors.append(f"extraction: {exc}")
                extraction = _fallback(active_caption, "", "")
        else:
            status = "failed"
            extraction = None

        return PipelineResult(
            shortcode=shortcode,
            url=canonical_url,
            status=status,
            caption=active_caption,
            uploader=active_uploader,
            transcript=transcript,
            ocr_text=ocr_text,
            language=language,
            extraction=extraction,
            errors=errors,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
