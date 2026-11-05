"""Utilities for system dependencies such as ffmpeg."""

import shutil

from app.pipeline.errors import FfmpegMissing


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is found on PATH, False otherwise."""
    return shutil.which("ffmpeg") is not None


def ensure_ffmpeg() -> None:
    """Ensure ffmpeg is available on PATH.

    Raises:
        FfmpegMissing: if ffmpeg is not installed or not found on PATH.
    """
    if not check_ffmpeg():
        raise FfmpegMissing(
            "ffmpeg is required for media merging and audio extraction but was not found on PATH. "
            "Install instructions:\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt update && sudo apt install -y ffmpeg"
        )

