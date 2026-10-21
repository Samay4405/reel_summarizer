# ReelBrief

ReelBrief turns saved Instagram reel links into short summaries and actionable resources.
Phase 1 provides the testable processing pipeline and CLI. Later phases will add the API,
Telegram bot, web app, and playlist integrations.

## Phase 1 setup

Prerequisites: Python 3.11+, `ffmpeg` on `PATH`, and (for live processing) enough disk/RAM
for the configured faster-whisper and EasyOCR models.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
```

Copy `backend\.env.example` to `.env` and set `ANTHROPIC_API_KEY` for Claude extraction.
Without a key, the CLI uses a deterministic offline fallback so URL and cleanup behavior can
be tested without external services.

Run the CLI:

```powershell
$env:PYTHONPATH = "backend"
python -m app.cli https://www.instagram.com/reel/SHORTCODE/
```

Run tests:

```powershell
$env:PYTHONPATH = "backend"
pytest backend\tests
```

The downloader uses a temporary directory and removes it in `finally`, including after
failures. Only the thumbnail is retained under `data\thumbnails`; video files are not stored.
This is a personal-use tool. Instagram's terms apply to the download step; it does not log
into Instagram, bypass access controls, scrape at scale, or process private reels.
