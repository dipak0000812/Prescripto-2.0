"""
Slice 3 — Ingest + Quality Check
Deterministic image quality gates. No ML model.
Per ML-ARCHITECTURE.md: Laplacian variance + histogram spread.
"""

import cv2
import numpy as np
from PIL import Image


def _load_grayscale(image_path: str) -> np.ndarray:
    """Load via PIL (handles mislabeled formats), convert to grayscale numpy array."""
    pil_img = Image.open(image_path).convert("L")  # "L" = grayscale
    return np.array(pil_img)


def check_blur(image_path: str, threshold: float = 100.0) -> tuple[bool, float]:
    img = _load_grayscale(image_path)
    variance = cv2.Laplacian(img, cv2.CV_64F).var()
    return variance >= threshold, variance


def check_exposure(image_path: str, low_thresh: float = 30, high_thresh: float = 250) -> tuple[bool, float]:
    img = _load_grayscale(image_path)
    mean_brightness = np.mean(img)
    is_ok = low_thresh <= mean_brightness <= high_thresh
    return is_ok, mean_brightness


def run_quality_check(image_path: str) -> dict:
    sharp_ok, blur_score = check_blur(image_path)
    exposure_ok, brightness = check_exposure(image_path)
    return {
        "image": image_path,
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