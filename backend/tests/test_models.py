"""Tests for Whisper and OCR lazy-loaded singletons."""

import sys
from unittest.mock import MagicMock

import pytest
from app.pipeline.models import clear_model_caches, get_ocr_reader, get_whisper_model


def test_whisper_model_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_model_caches()
    created_instances = []

    def fake_whisper(model_name: str, device: str = "cpu") -> MagicMock:
        inst = MagicMock(name=f"whisper_{model_name}_{device}")
        created_instances.append(inst)
        return inst

    mock_whisper_mod = MagicMock()
    mock_whisper_mod.WhisperModel = fake_whisper
    monkeypatch.setitem(sys.modules, "faster_whisper", mock_whisper_mod)

    m1 = get_whisper_model("small", "cpu")
    m2 = get_whisper_model("small", "cpu")
    assert m1 is m2
    assert len(created_instances) == 1

    # Different params create a new cached entry
    m3 = get_whisper_model("tiny", "cpu")
    assert m3 is not m1
    assert len(created_instances) == 2


def test_ocr_reader_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_model_caches()
    created_instances = []

    def fake_reader(languages: list[str], gpu: bool = False) -> MagicMock:
        inst = MagicMock(name=f"easyocr_{languages}_{gpu}")
        created_instances.append(inst)
        return inst

    mock_easyocr_mod = MagicMock()
    mock_easyocr_mod.Reader = fake_reader
    monkeypatch.setitem(sys.modules, "easyocr", mock_easyocr_mod)

    r1 = get_ocr_reader(("en",), gpu=False)
    r2 = get_ocr_reader(("en",), gpu=False)
    assert r1 is r2
    assert len(created_instances) == 1
