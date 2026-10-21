"""Temporary media fetching through yt-dlp."""

from pathlib import Path
from typing import Any


def fetch_reel(url: str, temp_dir: Path, thumbnail_path: Path) -> dict[str, Any]:
    """Fetch media metadata and a thumbnail, retaining no video after the call.

    The caller owns the temporary directory and must remove it in a ``finally`` block.
    """
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is required for live fetching. Install backend/requirements.txt."
        ) from exc

    temp_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(temp_dir / "%(id)s.%(ext)s")
    options = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": output_template,
        "writethumbnail": True,
        "format": "bestvideo*+bestaudio/best",
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)

    thumbnail_candidates = list(temp_dir.glob("*.jpg")) + list(temp_dir.glob("*.jpeg"))
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

    return {
        "audio_path": next(iter(temp_dir.glob("*.mp3")), None),
        "media_path": next(
            (path for path in temp_dir.iterdir() if path.suffix.lower() in {".mp4", ".webm", ".mkv"}),
            None,
        ),
        "caption": info.get("description") or "",
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "thumbnail_path": thumbnail_path if thumbnail_path.exists() else None,
    }
