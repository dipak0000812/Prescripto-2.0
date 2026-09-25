"""
Slice 3 — Ingest + Quality Check
Deterministic image quality gates. No ML model.
Per ML-ARCHITECTURE.md: Laplacian variance + histogram spread.
"""

import cv2
import numpy as np


def check_blur(image_path: str, threshold: float = 100.0) -> tuple[bool, float]:
    """
    Laplacian variance: low variance = blurry image.
    Returns (is_sharp_enough, variance_score).
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    variance = cv2.Laplacian(img, cv2.CV_64F).var()
    return variance >= threshold, variance


def check_exposure(image_path: str, low_thresh: float = 30, high_thresh: float = 225) -> tuple[bool, float]:
    """
    Histogram spread: checks mean brightness isn't too dark or too washed out.
    Returns (is_well_exposed, mean_brightness).
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    mean_brightness = np.mean(img)
    is_ok = low_thresh <= mean_brightness <= high_thresh
    return is_ok, mean_brightness


def run_quality_check(image_path: str) -> dict:
    """Runs all quality gates, returns a report dict."""
    sharp_ok, blur_score = check_blur(image_path)
    exposure_ok, brightness = check_exposure(image_path)

    return {
        "image": image_path,
        "sharp_ok": sharp_ok,
        "blur_score": round(blur_score, 2),
        "exposure_ok": exposure_ok,
        "brightness": round(brightness, 2),
        "passed": sharp_ok and exposure_ok,
    }


if __name__ == "__main__":
    test_image = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset\1_test.jpg"
    result = run_quality_check(test_image)
    print(result)