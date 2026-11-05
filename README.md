# ReelBrief

ReelBrief turns saved Instagram reel links into short summaries and actionable resources.
Phase 1 provides the testable processing pipeline and CLI. ReelBrief v2 introduces a Chrome Extension backed by the local FastAPI pipeline.

## Prerequisites

1. **Python 3.11 or 3.12** in a virtual environment (Python 3.13 currently has wheel compatibility limitations on Windows for torch/ctranslate2).
2. **`ffmpeg` on system `PATH`**:
   - **Windows**: `winget install Gyan.FFmpeg` (or `choco install ffmpeg` / `scoop install ffmpeg`)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt update && sudo apt install -y ffmpeg`
3. (For live processing) Sufficient disk space and RAM for the configured faster-whisper and EasyOCR models.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install --no-build-isolation -e .
```

Copy `backend\.env.example` to `.env` and set `ANTHROPIC_API_KEY` for Claude extraction:

```powershell
cp backend\.env.example .env
```

Without an API key, the pipeline uses a deterministic offline fallback so URL normalization, media cleanup, and error handling can be tested without external services.

## Running Tests

Run the full unit test suite from the repository root:

```powershell
pytest
```

## Running the CLI

Run the pipeline from the command line:

```powershell
python -m app.cli https://www.instagram.com/reel/SHORTCODE/
```

Options:
- `--caption "..."`: Provide a caption extracted directly from the web page (enables `partial` extraction if media download is blocked).
- `--uploader "username"`: Associate uploader metadata.
- `--cookies-file "data/cookies.txt"`: Path to Netscape cookies file for authenticated Instagram downloads.
- `--thumbnail-dir "data/thumbnails"`: Directory where 480x480 thumbnails are retained.

## Privacy & Storage Constraints

- Video media is strictly written to an ephemeral temporary directory and purged in `finally` blocks upon both success and failure.
- Only the 480x480 thumbnail is retained under `data\thumbnails`; raw video files are **never** stored permanently on disk.
- ReelBrief is a personal-use tool. Instagram's terms of service apply to the download step; it avoids mass scraping, fingerprint evasion, or accessing private reels.
