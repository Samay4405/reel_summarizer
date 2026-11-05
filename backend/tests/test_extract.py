"""Tests for extraction logic, schema validation, tool-use parsing, fence stripping, and retries."""

import json
import sys
from unittest.mock import MagicMock

import pytest
from app.pipeline.extract import _fallback, extract_information, strip_code_fences


def test_strip_code_fences() -> None:
    raw_json = '{"key": "value"}'
    assert strip_code_fences(raw_json) == raw_json
    assert strip_code_fences(f"```json\n{raw_json}\n```") == raw_json
    assert strip_code_fences(f"```\n{raw_json}\n```") == raw_json
    assert strip_code_fences('  ```json  \n{\n  "a": 1\n}\n```  ') == '{\n  "a": 1\n}'


def test_offline_extraction_is_schema_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = extract_information("Use Cursor AI to code faster.", "", "")
    assert result.category == "other"
    assert "Cursor" in result.short_summary
    assert result.worth_watching is True


def test_offline_fallback_empty_content() -> None:
    result = _fallback("", "", "")
    assert result.category == "other"
    assert result.worth_watching is False
    assert "No usable content" in result.worth_watching_reason


def test_claude_tool_use_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    valid_payload = {
        "short_summary": "Guide to Docker",
        "detailed_summary": "Comprehensive overview of Docker containers and images.",
        "category": "coding",
        "tools": [{"name": "Docker", "what_it_does": "Containerization platform"}],
        "github_repos": [],
        "websites": [],
        "songs": [],
        "youtube_resources": [],
        "books_or_courses": [],
        "action_items": ["Install Docker Desktop"],
        "tags": ["docker", "devops"],
        "worth_watching": True,
        "worth_watching_reason": "High quality tutorial",
    }

    mock_client = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_reel_insights"
    mock_block.input = valid_payload

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_client.messages.create.return_value = mock_response

    mock_anthropic_mod = MagicMock()
    mock_anthropic_mod.Anthropic.return_value = mock_client
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic_mod)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    result = extract_information("Docker tutorial", "", "")
    assert result.category == "coding"
    assert len(result.tools) == 1
    assert result.tools[0].name == "Docker"
    assert mock_client.messages.create.call_count == 1


def test_claude_retries_on_initial_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    invalid_block = MagicMock()
    invalid_block.type = "tool_use"
    invalid_block.name = "extract_reel_insights"
    invalid_block.input = {"category": "invalid_category"}  # Missing required fields

    valid_payload = {
        "short_summary": "Recovered summary",
        "detailed_summary": "Detailed info after retry",
        "category": "ai_tools",
        "tools": [],
        "github_repos": [],
        "websites": [],
        "songs": [],
        "youtube_resources": [],
        "books_or_courses": [],
        "action_items": [],
        "tags": ["ai"],
        "worth_watching": True,
        "worth_watching_reason": "Helpful AI tool review",
    }
    valid_block = MagicMock()
    valid_block.type = "tool_use"
    valid_block.name = "extract_reel_insights"
    valid_block.input = valid_payload

    mock_resp_1 = MagicMock()
    mock_resp_1.content = [invalid_block]
    mock_resp_2 = MagicMock()
    mock_resp_2.content = [valid_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [mock_resp_1, mock_resp_2]

    mock_anthropic_mod = MagicMock()
    mock_anthropic_mod.Anthropic.return_value = mock_client
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic_mod)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    result = extract_information("AI tool caption", "", "")
    assert result.category == "ai_tools"
    assert result.short_summary == "Recovered summary"
    assert mock_client.messages.create.call_count == 2
