"""Instagram URL normalization."""

import re
from urllib.parse import urlparse


_PATH_PATTERN = re.compile(r"^/(?:reel|reels|p|tv)/([^/?#]+)/?", re.IGNORECASE)


def normalize_instagram_url(url: str) -> tuple[str, str]:
    """Return the canonical Instagram URL and shortcode.

    Raises:
        ValueError: if the URL is not an Instagram reel-like URL.
    """
    candidate = url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in {
        "instagram.com",
        "www.instagram.com",
    }:
        raise ValueError("Enter a valid Instagram reel, post, or video URL.")

    match = _PATH_PATTERN.match(parsed.path)
    if not match:
        raise ValueError("The Instagram URL must contain /reel/, /reels/, /p/, or /tv/.")

    shortcode = match.group(1)
    return f"https://www.instagram.com/reel/{shortcode}/", shortcode
