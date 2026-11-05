"""Tests for ReelBrief typed error hierarchy and download error mapping."""

import pytest
from app.pipeline.errors import (
    FfmpegMissing,
    LoginRequired,
    MediaUnavailable,
    PrivateOrDeleted,
    RateLimited,
    ReelBriefError,
)
from app.pipeline.fetch import _map_download_error


def test_error_hierarchy() -> None:
    assert issubclass(LoginRequired, ReelBriefError)
    assert issubclass(RateLimited, ReelBriefError)
    assert issubclass(PrivateOrDeleted, ReelBriefError)
    assert issubclass(MediaUnavailable, ReelBriefError)
    assert issubclass(FfmpegMissing, ReelBriefError)


@pytest.mark.parametrize(
    "msg,expected_cls",
    [
        ("ffmpeg is not installed or not found", FfmpegMissing),
        ("Please log in to instagram to access this post", LoginRequired),
        ("HTTP Error 429: Too Many Requests", RateLimited),
        ("ERROR: [Instagram] DEMO123: This post is private or unavailable (404)", PrivateOrDeleted),
        ("Connection reset by peer", MediaUnavailable),
    ],
)
def test_map_download_error(msg: str, expected_cls: type) -> None:
    mapped = _map_download_error(Exception(msg))
    assert isinstance(mapped, expected_cls)
