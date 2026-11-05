"""Tests for yt-dlp fetch options, cookie forwarding, and media discovery."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.pipeline.errors import LoginRequired
from app.pipeline.fetch import fetch_reel


def test_fetch_reel_passes_cookies(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured_options = {}

    class FakeYoutubeDL:
        def __init__(self, options: dict) -> None:
            nonlocal captured_options
            captured_options = options

        def __enter__(self) -> "FakeYoutubeDL":
            return self

        def __exit__(self, *args) -> None:
            pass

        def extract_info(self, url: str, download: bool = True) -> dict:
            return {"description": "A demo reel", "uploader": "creator_123"}

    mock_ytdlp = MagicMock()
    mock_ytdlp.YoutubeDL = FakeYoutubeDL
    monkeypatch.setitem(sys.modules, "yt_dlp", mock_ytdlp)

    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text("# Netscape HTTP Cookie File", encoding="utf-8")
    temp_dir = tmp_path / "temp"
    media_file = temp_dir / "ABC123.mp4"
    temp_dir.mkdir()
    media_file.write_bytes(b"dummy-video-data")
    thumbnail_path = tmp_path / "thumb.jpg"

    result = fetch_reel(
        "https://www.instagram.com/reel/ABC123/",
        temp_dir=temp_dir,
        thumbnail_path=thumbnail_path,
        cookies_file=cookies_file,
    )

    assert captured_options.get("cookiefile") == str(cookies_file)
    assert result["media_path"] == media_file
    assert result["caption"] == "A demo reel"
    assert result["uploader"] == "creator_123"


def test_fetch_reel_raises_login_required(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FailingYoutubeDL:
        def __init__(self, options: dict) -> None:
            pass

        def __enter__(self) -> "FailingYoutubeDL":
            return self

        def __exit__(self, *args) -> None:
            pass

        def extract_info(self, url: str, download: bool = True) -> dict:
            raise Exception("Please log in to Instagram to view this content.")

    mock_ytdlp = MagicMock()
    mock_ytdlp.YoutubeDL = FailingYoutubeDL
    monkeypatch.setitem(sys.modules, "yt_dlp", mock_ytdlp)

    temp_dir = tmp_path / "temp"
    thumbnail_path = tmp_path / "thumb.jpg"

    with pytest.raises(LoginRequired):
        fetch_reel("https://www.instagram.com/reel/ABC123/", temp_dir, thumbnail_path)
