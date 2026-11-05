"""Tests for ffmpeg presence checking and error generation."""

from unittest.mock import patch

import pytest
from app.pipeline.errors import FfmpegMissing
from app.pipeline.ffmpeg_check import check_ffmpeg, ensure_ffmpeg


def test_check_ffmpeg_reflects_which(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/ffmpeg" if cmd == "ffmpeg" else None)
    assert check_ffmpeg() is True

    monkeypatch.setattr("shutil.which", lambda cmd: None)
    assert check_ffmpeg() is False


def test_ensure_ffmpeg_raises_on_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    with pytest.raises(FfmpegMissing) as exc_info:
        ensure_ffmpeg()
    assert "winget install Gyan.FFmpeg" in str(exc_info.value)
