"""Audio transcription stage using faster-whisper."""

from pathlib import Path

from app.pipeline.ffmpeg_check import ensure_ffmpeg
from app.pipeline.models import get_whisper_model


def transcribe_audio(
    media_path: Path | None,
    model_name: str | None = None,
    device: str | None = None,
) -> tuple[str, str | None]:
    """Transcribe speech from a media file (video container or audio file).

    Returns ``(transcript, detected_language)``.
    Missing media is treated as a valid no-speech result.
    """
    if media_path is None or not media_path.exists():
        return "", None

    ensure_ffmpeg()
    model = get_whisper_model(model_name=model_name, device=device)
    segments, info = model.transcribe(str(media_path))
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text, getattr(info, "language", None)
