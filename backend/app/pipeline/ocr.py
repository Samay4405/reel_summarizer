"""Sampled-frame OCR stage."""

from pathlib import Path


def extract_ocr(media_path: Path | None, max_frames: int = 15) -> str:
    """Read visible text from sampled frames, de-duplicating repeated lines."""
    if media_path is None or not media_path.exists():
        return ""
    try:
        import easyocr
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "EasyOCR and OpenCV are required for OCR. Install backend/requirements.txt."
        ) from exc

    reader = easyocr.Reader(["en"], gpu=False)
    capture = cv2.VideoCapture(str(media_path))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 1
    duration = frame_count / fps if frame_count else 0
    sample_count = min(max_frames, max(1, int(duration / 2) + 1))
    lines: list[str] = []
    for index in range(sample_count):
        capture.set(cv2.CAP_PROP_POS_MSEC, index * 2000)
        success, frame = capture.read()
        if not success:
            continue
        lines.extend(text.strip() for text in reader.readtext(frame, detail=0) if text.strip())
    capture.release()

    unique_lines: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = " ".join(line.lower().split())
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)
    return "\n".join(unique_lines)
