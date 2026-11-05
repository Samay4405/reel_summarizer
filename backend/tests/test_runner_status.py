"""Tests for runner outcome statuses (processed, partial, failed) and cleanup."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.pipeline import runner
from app.pipeline.errors import LoginRequired


def test_runner_full_processed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    created_dir = None

    def fake_fetch(url, temp_dir, thumbnail_path, cookies_file=None):
        nonlocal created_dir
        created_dir = temp_dir
        media = temp_dir / "download.mp4"
        media.write_bytes(b"dummy")
        return {"media_path": media, "caption": "Awesome reel", "uploader": "creator"}

    monkeypatch.setattr(runner, "fetch_reel", fake_fetch)
    monkeypatch.setattr(runner, "extract_ocr", lambda path: "VISIBLE OCR")
    monkeypatch.setattr(runner, "transcribe_audio", lambda path, model_name=None, device=None: ("Transcribed audio", "en"))

    result = runner.process_reel("https://www.instagram.com/reel/DEMO123/", thumbnail_dir=tmp_path)
    assert result.status == "processed"
    assert result.shortcode == "DEMO123"
    assert result.caption == "Awesome reel"
    assert result.transcript == "Transcribed audio"
    assert result.ocr_text == "VISIBLE OCR"
    assert result.extraction is not None
    assert not created_dir.exists()


def test_runner_partial_when_media_fails_but_caption_provided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    created_dir = None

    def failing_fetch(url, temp_dir, thumbnail_path, cookies_file=None):
        nonlocal created_dir
        created_dir = temp_dir
        raise LoginRequired("Instagram login required")

    monkeypatch.setattr(runner, "fetch_reel", failing_fetch)

    result = runner.process_reel(
        "https://www.instagram.com/reel/PARTIAL123/",
        thumbnail_dir=tmp_path,
        caption="Caption collected directly by extension from web page",
        uploader="extension_user",
    )

    assert result.status == "partial"
    assert result.shortcode == "PARTIAL123"
    assert result.caption == "Caption collected directly by extension from web page"
    assert result.extraction is not None
    assert "Caption collected" in result.extraction.short_summary
    assert any("fetch: Instagram login required" in err for err in result.errors)
    assert not created_dir.exists()


def test_runner_failed_when_both_media_and_caption_fail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    created_dir = None

    def failing_fetch(url, temp_dir, thumbnail_path, cookies_file=None):
        nonlocal created_dir
        created_dir = temp_dir
        raise LoginRequired("Instagram login required")

    monkeypatch.setattr(runner, "fetch_reel", failing_fetch)

    result = runner.process_reel(
        "https://www.instagram.com/reel/FAIL123/",
        thumbnail_dir=tmp_path,
        caption="",
    )

    assert result.status == "failed"
    assert result.shortcode == "FAIL123"
    assert result.extraction is None
    assert len(result.errors) > 0
    assert not created_dir.exists()

