"""
Slice 3 — Ingest + Quality Check
Deterministic image quality gates. No ML model.
Per ML-ARCHITECTURE.md: Laplacian variance + histogram spread.
"""

import cv2
import numpy as np
from PIL import Image


from io import BytesIO
from typing import Union

def _load_grayscale(image_input: Union[str, bytes, Image.Image]) -> np.ndarray:
    """Load via PIL (handles bytes, PIL Image, or file path), convert to grayscale numpy array."""
    if isinstance(image_input, Image.Image):
        pil_img = image_input.convert("L")
    elif isinstance(image_input, (bytes, bytearray)):
        pil_img = Image.open(BytesIO(image_input)).convert("L")
    else:
        pil_img = Image.open(image_input).convert("L")
    return np.array(pil_img)


def check_blur(image_input: Union[str, bytes, Image.Image], threshold: float = 100.0) -> tuple[bool, float]:
    img = _load_grayscale(image_input)
    variance = cv2.Laplacian(img, cv2.CV_64F).var()
    return variance >= threshold, float(variance)


def check_exposure(image_input: Union[str, bytes, Image.Image], low_thresh: float = 20.0, high_thresh: float = 255.0) -> tuple[bool, float]:
    img = _load_grayscale(image_input)
    mean_brightness = float(np.mean(img))
    is_ok = low_thresh <= mean_brightness <= high_thresh
    return is_ok, mean_brightness


def run_quality_check(image_input: Union[str, bytes, Image.Image]) -> dict:
    sharp_ok, blur_score = check_blur(image_input)
    exposure_ok, brightness = check_exposure(image_input)
    return {
        "image": str(image_input) if isinstance(image_input, str) else "<bytes>",
        "sharp_ok": bool(sharp_ok),
        "blur_score": round(float(blur_score), 2),
        "exposure_ok": bool(exposure_ok),
        "brightness": round(float(brightness), 2),
        "passed": bool(sharp_ok and exposure_ok),
    }


if __name__ == "__main__":
    test_image = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset\1_test.jpg"
    result = run_quality_check(test_image)
    print(result)