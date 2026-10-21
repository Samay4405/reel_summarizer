"""Audio transcription stage."""

from pathlib import Path


def transcribe_audio(audio_path: Path | None, model_name: str = "small") -> tuple[str, str | None]:
    """Transcribe audio and return ``(text, detected_language)``.

    Missing audio is a valid no-speech result.
    """
    if audio_path is None or not audio_path.exists():
        return "", None
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for transcription. Install backend/requirements.txt."
        ) from exc

    model = WhisperModel(model_name)
    segments, info = model.transcribe(str(audio_path))
    return " ".join(segment.text.strip() for segment in segments).strip(), info.language
