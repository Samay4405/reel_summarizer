"""Temporary media fetching through yt-dlp with cookie and error support."""

import os
from pathlib import Path
from typing import Any

from app.pipeline.errors import (
    FfmpegMissing,
    LoginRequired,
    MediaUnavailable,
    PrivateOrDeleted,
    RateLimited,
)


def _map_download_error(exc: Exception) -> Exception:
    """Map yt-dlp errors to typed ReelBrief pipeline exceptions."""
    err_str = str(exc).lower()
    if "ffmpeg" in err_str and any(w in err_str for w in ["not found", "missing", "install"]):
        return FfmpegMissing(f"ffmpeg required by yt-dlp: {exc}")
    if any(term in err_str for term in ["login", "checkpoint", "log in", "sign in", "authenticate"]):
        return LoginRequired(f"Instagram requires login to access this reel: {exc}")
    if any(term in err_str for term in ["429", "rate limit", "too many requests"]):
        return RateLimited(f"Instagram rate limited the download: {exc}")
    if any(term in err_str for term in ["404", "not found", "private", "deleted", "unavailable"]):
        return PrivateOrDeleted(f"Reel is private, deleted, or unavailable: {exc}")
    return MediaUnavailable(f"Media download failed: {exc}")


def fetch_reel(
    url: str,
    temp_dir: Path,
    thumbnail_path: Path,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    """Fetch media metadata and thumbnail via yt-dlp, retaining no video after caller cleans up.

    Args:
        url: Canonical Instagram reel URL.
        temp_dir: Directory owned by caller for temporary media storage.
        thumbnail_path: Target path for the retained thumbnail image.
        cookies_file: Optional path to Netscape-format cookies file for authenticated downloads.

    Returns:
        Dictionary with media_path, caption, uploader, duration, and thumbnail_path.
    """
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is required for live fetching. Install backend/requirements.txt."
        ) from exc

    resolved_cookies = cookies_file or os.getenv("COOKIES_FILE")
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(temp_dir / "%(id)s.%(ext)s")

    options: dict[str, Any] = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": output_template,
        "writethumbnail": True,
        "format": "bestvideo*+bestaudio/best",
        "overwrites": True,
    }

    if resolved_cookies:
        cookie_path = Path(resolved_cookies)
        if cookie_path.exists():
            options["cookiefile"] = str(cookie_path)

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
    except Exception as exc:
        raise _map_download_error(exc) from exc

    # Locate downloaded thumbnail and normalize
    thumbnail_candidates = list(temp_dir.glob("*.jpg")) + list(temp_dir.glob("*.jpeg")) + list(temp_dir.glob("*.webp"))
    if thumbnail_candidates:
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image

            with Image.open(thumbnail_candidates[0]) as image:
                image.convert("RGB").thumbnail((480, 480))
                image.save(thumbnail_path, format="JPEG", quality=85)
        except ImportError as exc:
            raise RuntimeError(
                "Pillow is required to save normalized thumbnails. Install backend/requirements.txt."
            ) from exc

    # Video containers and audio files
    media_extensions = {".mp4", ".webm", ".mkv", ".mov", ".m4a", ".mp3"}
    media_path = next(
        (path for path in temp_dir.iterdir() if path.suffix.lower() in media_extensions),
        None,
    )

    return {
        "media_path": media_path,
        "caption": info.get("description") or "",
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "thumbnail_path": thumbnail_path if thumbnail_path.exists() else None,
    }
