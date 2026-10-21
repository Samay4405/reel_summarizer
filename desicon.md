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
