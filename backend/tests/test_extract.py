from app.pipeline.extract import extract_information


def test_offline_extraction_is_schema_valid(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = extract_information("Use Cursor AI to code faster.", "", "")
    assert result.category == "other"
    assert "Cursor" in result.short_summary
