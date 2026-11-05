"""Lazy-loaded singleton models for transcription and OCR."""

import functools
import os
from typing import Any


@functools.lru_cache(maxsize=4)
def get_whisper_model(model_name: str | None = None, device: str | None = None) -> Any:
    """Return a cached WhisperModel instance.

    Args:
        model_name: Model size or identifier (defaults to WHISPER_MODEL env or 'small').
        device: Device to run on (defaults to WHISPER_DEVICE env or 'cpu').
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for transcription. Install backend/requirements.txt."
        ) from exc

    resolved_model = model_name or os.getenv("WHISPER_MODEL", "small")
    resolved_device = device or os.getenv("WHISPER_DEVICE", "cpu")
    return WhisperModel(resolved_model, device=resolved_device)


@functools.lru_cache(maxsize=4)
def get_ocr_reader(languages: tuple[str, ...] = ("en",), gpu: bool = False) -> Any:
    """Return a cached EasyOCR Reader instance."""
    try:
        import easyocr
    except ImportError as exc:
        raise RuntimeError(
            "EasyOCR is required for OCR extraction. Install backend/requirements.txt."
        ) from exc

    return easyocr.Reader(list(languages), gpu=gpu)


def preload_models() -> None:
    """Pre-warm model caches at application startup."""
    get_whisper_model()
    get_ocr_reader()


def clear_model_caches() -> None:
    """Clear singleton caches (primarily for unit tests and resource reclamation)."""
    get_whisper_model.cache_clear()
    get_ocr_reader.cache_clear()

