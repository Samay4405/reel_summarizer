"""Sampled-frame OCR stage with swappable engine interface."""

from pathlib import Path
from typing import Protocol

from app.pipeline.models import get_ocr_reader


class OCREngine(Protocol):
    """Protocol for pluggable video frame OCR engines."""

    def extract_text(self, media_path: Path, max_frames: int = 15) -> str:
        """Extract de-duplicated visible text from sampled video frames."""
        ...


class EasyOCREngine:
    """Default OCR engine using OpenCV for frame sampling and EasyOCR for text detection."""

    def __init__(self, languages: tuple[str, ...] = ("en",), gpu: bool = False) -> None:
        self.languages = languages
        self.gpu = gpu

    def extract_text(self, media_path: Path, max_frames: int = 15) -> str:
        if not media_path.exists():
            return ""

        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                "OpenCV (opencv-python-headless) is required for OCR frame capture."
            ) from exc

        reader = get_ocr_reader(self.languages, gpu=self.gpu)
        capture = cv2.VideoCapture(str(media_path))
        if not capture.isOpened():
            return ""

        try:
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = capture.get(cv2.CAP_PROP_FPS) or 1
            duration = frame_count / fps if frame_count > 0 else 0
            sample_count = min(max_frames, max(1, int(duration / 2) + 1))

            lines: list[str] = []
            for index in range(sample_count):
                capture.set(cv2.CAP_PROP_POS_MSEC, index * 2000)
                success, frame = capture.read()
                if not success or frame is None:
                    continue
                extracted = reader.readtext(frame, detail=0)
                lines.extend(text.strip() for text in extracted if text and text.strip())

            unique_lines: list[str] = []
            seen: set[str] = set()
            for line in lines:
                key = " ".join(line.lower().split())
                if key and key not in seen:
                    seen.add(key)
                    unique_lines.append(line)
            return "\n".join(unique_lines)
        finally:
            capture.release()


_DEFAULT_ENGINE = EasyOCREngine()


def extract_ocr(
    media_path: Path | None,
    max_frames: int = 15,
    engine: OCREngine | None = None,
) -> str:
    """Read visible text from sampled frames, de-duplicating repeated lines."""
    if media_path is None or not media_path.exists():
        return ""
    active_engine = engine or _DEFAULT_ENGINE
    return active_engine.extract_text(media_path, max_frames=max_frames)
