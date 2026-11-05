"""Command-line entry point for ReelBrief pipeline."""

import argparse
import json
from pathlib import Path

from app.pipeline.runner import process_reel


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize an Instagram reel with ReelBrief.")
    parser.add_argument("url", help="Instagram /reel/, /reels/, /p/, or /tv/ URL")
    parser.add_argument("--thumbnail-dir", default="data/thumbnails", help="Directory for thumbnails")
    parser.add_argument("--cookies-file", default=None, help="Path to Netscape cookies.txt file")
    parser.add_argument("--caption", default=None, help="Pre-extracted post caption (e.g. from browser)")
    parser.add_argument("--uploader", default=None, help="Pre-extracted uploader username")
    args = parser.parse_args()

    result = process_reel(
        args.url,
        thumbnail_dir=Path(args.thumbnail_dir),
        cookies_file=args.cookies_file,
        caption=args.caption,
        uploader=args.uploader,
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
