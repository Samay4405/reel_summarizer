"""Command-line entry point for Phase 1."""

import argparse
import json

from app.pipeline.runner import process_reel


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize an Instagram reel with ReelBrief.")
    parser.add_argument("url", help="Instagram /reel/, /reels/, /p/, or /tv/ URL")
    parser.add_argument("--thumbnail-dir", default="data/thumbnails")
    args = parser.parse_args()
    result = process_reel(args.url, thumbnail_dir=args.thumbnail_dir)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
