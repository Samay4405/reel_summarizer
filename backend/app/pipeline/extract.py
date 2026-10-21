"""Claude extraction with schema validation and deterministic offline fallback."""

import json
import os
from typing import Any

from app.schemas import Extraction


def _fallback(caption: str, transcript: str, ocr_text: str) -> Extraction:
    content = " ".join(part for part in (caption, transcript, ocr_text) if part).strip()
    summary = content[:240] or "No caption, speech, or on-screen text was available."
    return Extraction(
        short_summary=summary,
        detailed_summary=summary,
        category="other",
        action_items=[],
        tags=[],
        worth_watching=bool(content),
        worth_watching_reason="Content was available for review." if content else "No usable content was found.",
    )


def extract_information(caption: str, transcript: str, ocr_text: str) -> Extraction:
    """Extract actionable information, retrying once after invalid Claude JSON."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback(caption, transcript, ocr_text)
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic is required when ANTHROPIC_API_KEY is configured.") from exc

    prompt = (
        "Extract only information present in the supplied content. Return JSON matching this "
        "schema exactly; use empty lists for absent fields and never invent URLs, repos, or songs.\n"
        f"Caption:\n{caption}\nTranscript:\n{transcript}\nOCR:\n{ocr_text}"
    )
    client = Anthropic(api_key=api_key)
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            return Extraction.model_validate(json.loads(raw))
        except (json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
            last_error = exc
            if attempt == 0:
                prompt += "\nYour previous response was invalid. Return JSON only."
    raise RuntimeError(f"Claude returned invalid extraction JSON after retry: {last_error}") from last_error
