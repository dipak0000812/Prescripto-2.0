"""
Prescripto ML Service — FastAPI entrypoint.

Endpoints:
    GET  /health              → liveness / readiness
    POST /v1/ocr/recognize    → multipart image → OCR + calibration + span extraction
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from ml.app.config import settings
from ml.app.inference.calibration import TemperatureScalingCalibrator
from ml.app.ocr.paddle_runtime import PaddleOCRRuntime
from ml.app.preprocessing.quality import check_quality
from ml.app.extraction.spans import extract_prescription_fields


# ---------------------------------------------------------------------------
# Runtime singletons — initialised on startup, not at import time
# ---------------------------------------------------------------------------

_ocr_runtime: PaddleOCRRuntime | None = None
_calibrator: TemperatureScalingCalibrator | None = None
_startup_error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ocr_runtime, _calibrator, _startup_error
    if _calibrator is None:
        _calibrator = TemperatureScalingCalibrator()   # T=1.0 scaffold
    if _ocr_runtime is None and _startup_error is None:
        try:
            _ocr_runtime = PaddleOCRRuntime(device=settings.DEVICE)
        except Exception as exc:
            _startup_error = str(exc)
    yield
    # Cleanup (none needed for stateless OCR runtime)


app = FastAPI(
    title="Prescripto ML Service",
    version=settings.MODEL_VERSION,
    description="Independent OCR inference service for prescription image analysis.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health() -> dict[str, Any]:
    """
    Liveness and readiness probe.
    Returns 503 if the runtime failed to initialise.
    """
    if _startup_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": _startup_error},
        )
    return {
        "status": "healthy",
        "device": settings.DEVICE,
        "model_name": settings.MODEL_NAME,
        "model_version": settings.MODEL_VERSION,
    }


# ---------------------------------------------------------------------------
# POST /v1/ocr/recognize
# ---------------------------------------------------------------------------

@app.post("/v1/ocr/recognize", tags=["ocr"])
async def recognize(file: UploadFile = File(...)) -> JSONResponse:
    """
    Accept a prescription image and return:
      - quality gate result
      - OCR lines (text, bounding box, raw score)
      - calibrated confidence and FieldState per line
      - regex-extracted field spans per line

    Model / version are controlled by deployment configuration only —
    callers cannot select or override the model via this request.
    """
    if _ocr_runtime is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR runtime is not available",
        )

    image_bytes = await file.read()

    if len(image_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum allowed size of {settings.MAX_UPLOAD_BYTES} bytes",
        )

    # --- Quality gate --------------------------------------------------
    try:
        quality = check_quality(
            image_bytes,
            min_dimension=settings.MIN_IMAGE_DIMENSION,
            blank_threshold=settings.BLANK_CONTRAST_THRESHOLD,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # --- OCR inference -------------------------------------------------
    t_start = time.perf_counter()
    try:
        lines = _ocr_runtime.recognize_document(image_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR inference failed: {type(exc).__name__}",
        )
    latency_ms = int((time.perf_counter() - t_start) * 1000)

    # --- Calibration + extraction per line ----------------------------
    line_results = []
    for line in lines:
        raw_score = line.raw_score if line.raw_score is not None else 0.0
        calibrated_confidence = _calibrator.calibrate(raw_score)
        field_state = _calibrator.determine_state(calibrated_confidence)
        extracted_fields = extract_prescription_fields(line.text)

        line_results.append({
            "line_index": line.line_index,
            "text": line.text,
            "raw_score": line.raw_score,
            "calibrated_confidence": calibrated_confidence,
            "field_state": field_state.value,
            "box": list(line.box),
            "extracted_fields": extracted_fields,
        })

    return JSONResponse(content={
        "model_name": settings.MODEL_NAME,
        "model_version": settings.MODEL_VERSION,
        "latency_ms": latency_ms,
        "quality": {
            "width": quality.width,
            "height": quality.height,
            "is_blank": quality.is_blank,
            "passed": quality.passed,
        },
        "lines": line_results,
    })
