# ReelBrief critical decisions

This file records the important implementation choices made during the project and the
reason for each choice. It is intentionally named `desicon.md` as requested.

## Phase 1 decisions

### Separate, testable pipeline stages

Each stage lives in its own module (`normalize`, `fetch`, `transcribe`, `ocr`, and `extract`).
This keeps media/network integrations replaceable and lets pure behavior be tested without
downloading a reel.

### Temporary media only

The fetch stage writes to a temporary directory owned by the runner. The runner always
removes that directory in `finally`, including when a stage raises an exception. This
directly enforces the requirement that videos never remain on disk.

### Keep only thumbnails

The thumbnail destination is outside the temporary directory, so it is the only media
artifact that can survive processing. The Phase 1 fetch adapter saves metadata and the
thumbnail path, not the downloaded video.

### Canonical Instagram URLs

`/reel/`, `/reels/`, `/p/`, and `/tv/` are accepted, but every result uses
`https://www.instagram.com/reel/<shortcode>/`. Tracking query parameters are therefore
discarded and future database de-duplication can use the shortcode.

### Claude with an offline fallback

Claude is used when `ANTHROPIC_API_KEY` exists. Without it, a deterministic schema-valid
fallback makes local development and tests possible without credentials or network access.
The fallback is deliberately conservative and does not invent actionable resources.

### One retry for invalid Claude JSON

The extraction response is parsed and validated with Pydantic. A single corrective retry is
made when Claude returns invalid JSON, matching the brief while preventing unbounded API use.

### Optional heavyweight media dependencies

`yt-dlp`, faster-whisper, EasyOCR, and OpenCV are declared dependencies, but their imports
occur inside the stages. URL normalization and offline tests remain usable when model
packages are not installed, while live processing reports a readable stage error.

### Python package layout

The source lives under `backend/app`, and the CLI is `python -m app.cli` with
`PYTHONPATH=backend`. This mirrors the requested backend structure and leaves room for
FastAPI routers and database modules in later phases.


## Step 0 decisions (Stabilization & Chrome Extension Prep)

### Media container audio decoding for faster-whisper
- **What**: Removed dead `*.mp3` file search in `fetch.py` and pass the downloaded video container (`.mp4`, `.mkv`, etc.) directly to `faster-whisper`.
- **Why**: `yt-dlp` fetches video containers by default without extracting an `.mp3`, which previously caused Whisper to always receive `None` and return an empty transcript.
- **Alternatives rejected**: Extra subprocess conversion to `.mp3` via ffmpeg (incurs disk I/O overhead while Whisper natively reads media containers).

### Claude tool-use structured extraction
- **What**: Switched Claude extraction to use forced tool calling with `Extraction.model_json_schema()` as `input_schema`, plus markdown code fence stripping and validation error feedback on retry. Configurable via `ANTHROPIC_MODEL` (default `claude-haiku-5-5`).
- **Why**: Pure text prompting without schema definition caused schema hallucinations and JSON parsing errors. Forced tool choice guarantees schema compliance.
- **Alternatives rejected**: Regex JSON extraction without tool calling or schema validation.

### Typed error hierarchy and outcome statuses
- **What**: Added `LoginRequired`, `RateLimited`, `PrivateOrDeleted`, `MediaUnavailable`, and `FfmpegMissing`. `PipelineResult` tracks status (`processed`, `partial`, `failed`).
- **Why**: When media downloads fail, captions provided by the page context still provide valuable insight (`partial`). True failures with no content report `failed` instead of dummy successes.
- **Alternatives rejected**: Catch-all exceptions that mask failure root causes.

### Cached model singletons
- **What**: Managed `WhisperModel` and `EasyOCR.Reader` using cached singletons via `get_whisper_model()` and `get_ocr_reader()` with optional preloading.
- **Why**: Re-instantiating heavy ML models on every reel call incurred 15+ seconds of latency and memory bloat.
- **Alternatives rejected**: Top-level module variables (which cause import crashes when weights or optional packages are not installed).

### Cookie support for yt-dlp
- **What**: Support `COOKIES_FILE` in `.env` and `cookies_file` parameter in `fetch_reel`.
- **Why**: Enables authenticated requests to bypass Instagram's aggressive anonymous IP rate limits and login challenges.

### Project configuration with pyproject.toml
- **What**: Added `pyproject.toml` configuring package discovery and `tool.pytest.ini_options.pythonpath = ["backend"]`.
- **Why**: Allows running `pytest` and `python -m app.cli` directly from repository root without manual `PYTHONPATH` shell workarounds.
