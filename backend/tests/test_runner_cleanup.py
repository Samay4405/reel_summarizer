from pathlib import Path

from app.pipeline import runner


def test_runner_removes_temporary_media(monkeypatch, tmp_path: Path) -> None:
    created: dict[str, Path] = {}

    def fake_fetch(url, temp_dir, thumbnail_path):
        media = temp_dir / "download.mp4"
        media.write_bytes(b"temporary")
        created["dir"] = temp_dir
        return {"media_path": media, "caption": "caption"}

    monkeypatch.setattr(runner, "fetch_reel", fake_fetch)
    monkeypatch.setattr(runner, "extract_ocr", lambda path: "")
    monkeypatch.setattr(runner, "transcribe_audio", lambda path, model: ("", None))
    result = runner.process_reel("https://instagram.com/reel/ABC123/", tmp_path)
    assert result.shortcode == "ABC123"
    assert not created["dir"].exists()
