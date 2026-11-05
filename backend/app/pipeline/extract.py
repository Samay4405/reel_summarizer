"""Claude extraction with tool-use structured outputs, schema validation, and offline fallback."""

import json
import os
import re
from typing import Any

from pydantic import ValidationError

from app.schemas import Extraction


def strip_code_fences(text: str) -> str:
    """Remove markdown code blocks (e.g. ```json ... ```) from text."""
    trimmed = text.strip()
    match = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", trimmed, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return trimmed


def _fallback(caption: str, transcript: str, ocr_text: str) -> Extraction:
    """Deterministic offline fallback when ANTHROPIC_API_KEY is not configured."""
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


def extract_information(
    caption: str,
    transcript: str,
    ocr_text: str,
    api_key: str | None = None,
    model: str | None = None,
) -> Extraction:
    """Extract actionable information, utilizing Claude tool-use and retrying once on failure.

    Args:
        caption: Extracted post caption.
        transcript: Transcribed speech.
        ocr_text: Sampled on-screen OCR text.
        api_key: Optional Anthropic API key (defaults to ANTHROPIC_API_KEY env).
        model: Optional model name (defaults to ANTHROPIC_MODEL env or 'claude-haiku-5-5').

    Returns:
        Validated Extraction instance.
    """
    resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not resolved_key:
        return _fallback(caption, transcript, ocr_text)

    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic is required when ANTHROPIC_API_KEY is configured.") from exc

    resolved_model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    schema = Extraction.model_json_schema()
    tool_definition = {
        "name": "extract_reel_insights",
        "description": "Extract structured insights, tools, repositories, and resources from reel content.",
        "input_schema": schema,
    }

    base_prompt = (
        "Extract only information present in the supplied Instagram reel content.\n"
        "Never invent URLs, tools, songs, or repos not mentioned.\n\n"
        f"Caption:\n{caption or '(none)'}\n\n"
        f"Transcript:\n{transcript or '(none)'}\n\n"
        f"OCR Text:\n{ocr_text or '(none)'}"
    )

    client = Anthropic(api_key=resolved_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": base_prompt}]
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            response = client.messages.create(
                model=resolved_model,
                max_tokens=2000,
                tools=[tool_definition],
                tool_choice={"type": "tool", "name": "extract_reel_insights"},
                messages=messages,
            )

            # Look for tool_use block
            tool_input: dict[str, Any] | None = None
            for block in response.content:
                if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "extract_reel_insights":
                    tool_input = block.input
                    break

            # Fallback path if tool_use block was not returned
            if tool_input is None:
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        cleaned = strip_code_fences(block.text)
                        tool_input = json.loads(cleaned)
                        break

            if tool_input is None:
                raise ValueError("Claude response did not contain tool use or valid text content.")

            return Extraction.model_validate(tool_input)

        except (ValidationError, json.JSONDecodeError, ValueError, TypeError, IndexError) as exc:
            last_error = exc
            if attempt == 0:
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Failed extraction response: {exc}",
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous extraction failed schema validation: {exc}. "
                            "Please correct the output and call extract_reel_insights with valid fields strictly "
                            "matching the schema."
                        ),
                    }
                )

    raise RuntimeError(f"Claude extraction failed schema validation after retry: {last_error}") from last_error
