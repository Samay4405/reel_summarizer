import pytest

from app.pipeline.normalize import normalize_instagram_url


@pytest.mark.parametrize("path", ["/reel/ABC123/", "/reels/ABC123/?igsh=tracking", "/p/ABC123/", "/tv/ABC123/"])
def test_normalizes_supported_paths(path: str) -> None:
    url, shortcode = normalize_instagram_url(f"https://www.instagram.com{path}")
    assert url == "https://www.instagram.com/reel/ABC123/"
    assert shortcode == "ABC123"


def test_rejects_non_instagram_url() -> None:
    with pytest.raises(ValueError):
        normalize_instagram_url("https://example.com/reel/ABC123")
