"""
Image quality gate for the ML service.

Logic matches backend/prescripto/pipeline/engine.py handle_quality_check exactly:
- minimum dimension < 400 → poor quality
- pixel contrast range (grayscale max - min) < 5 → blank image

Dependency: Pillow only — no opencv required.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class QualityResult:
    width: int
    height: int
    is_blank: bool
    passed: bool
    blur_score: float | None = None
    brightness: float | None = None


def check_quality(image_bytes: bytes, min_dimension: int = 400, blank_threshold: int = 5) -> QualityResult:
    """
    Decode image and evaluate minimum quality criteria.

    Raises ValueError if image_bytes cannot be decoded by Pillow.
    """
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required by the ML service preprocessing") from error

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            gray = image.convert("L")
            extrema = gray.getextrema()
            is_blank = (extrema[1] - extrema[0] < blank_threshold)
    except Exception as error:
        raise ValueError("Uploaded image cannot be decoded") from error

    is_poor_quality = width < min_dimension or height < min_dimension or is_blank
    blur_score = None
    brightness = None

    try:
        from ml.ocr.quality_check import check_blur, check_exposure
        sharp_ok, blur_score = check_blur(image_bytes, threshold=100.0)
        exposure_ok, brightness = check_exposure(image_bytes, low_thresh=20.0, high_thresh=255.0)
        if not sharp_ok or not exposure_ok:
            is_poor_quality = True
    except Exception:
        pass

    return QualityResult(
        width=width,
        height=height,
        is_blank=is_blank,
        passed=not is_poor_quality,
        blur_score=blur_score,
        brightness=brightness,
    )
