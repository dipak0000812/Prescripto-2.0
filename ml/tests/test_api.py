"""
ML Service — HTTP API Tests.

Uses FastAPI TestClient with a MockOCRRuntime so PaddleOCR/PaddlePaddle
is NOT required to run these tests.  Only Pillow, FastAPI, and httpx
are needed.

Covers:
    - GET /health (healthy)
    - GET /health (unhealthy — startup error path)
    - POST /v1/ocr/recognize — valid PNG image
    - POST /v1/ocr/recognize — non-image file (422)
    - POST /v1/ocr/recognize — oversized payload (413)
    - POST /v1/ocr/recognize — malformed multipart (422)
    - POST /v1/ocr/recognize — response schema fields present
    - POST /v1/ocr/recognize — model_name / model_version from config
    - POST /v1/ocr/recognize — calibrated_confidence and field_state present
    - POST /v1/ocr/recognize — extracted_fields per line present
    - POST /v1/ocr/recognize — blank white image quality.passed == False
    - POST /v1/ocr/recognize — inference failure path (502)
"""
from __future__ import annotations

import io
import pytest

from fastapi.testclient import TestClient

from ml.app.ocr.paddle_runtime import OCRLine
import ml.app.main as app_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_png(width: int = 800, height: int = 600, fill: int = 128) -> bytes:
    """Produce a minimal valid PNG using only Pillow."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, height), color=(fill, fill, fill))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Augmentin 625 Duo 1 tab BD", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_blank_png(width: int = 800, height: int = 600) -> bytes:
    """All-white PNG — triggers blank detection."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class MockOCRRuntime:
    """Stand-in for PaddleOCRRuntime — deterministic output, no PaddleOCR installed."""

    def recognize_document(self, image_bytes: bytes) -> list[OCRLine]:
        if not image_bytes:
            raise ValueError("Empty image bytes")
        return [
            OCRLine(
                line_index=0,
                text="Augmentin 625 Duo 1 tab BD after food 5 days",
                raw_score=0.965,
                box=(40.0, 120.0, 620.0, 160.0),
            )
        ]


class FailingOCRRuntime:
    """Simulates a runtime that raises on recognize_document."""

    def recognize_document(self, image_bytes: bytes) -> list[OCRLine]:
        raise RuntimeError("GPU out of memory")


@pytest.fixture()
def client(monkeypatch):
    """TestClient with MockOCRRuntime injected — no real PaddleOCR."""
    monkeypatch.setattr(app_module, "_ocr_runtime", MockOCRRuntime())
    monkeypatch.setattr(app_module, "_startup_error", None)
    with TestClient(app_module.app, raise_server_exceptions=False) as tc:
        yield tc


@pytest.fixture()
def unhealthy_client(monkeypatch):
    monkeypatch.setattr(app_module, "_ocr_runtime", None)
    monkeypatch.setattr(app_module, "_startup_error", "PaddleOCR failed to load")
    with TestClient(app_module.app, raise_server_exceptions=False) as tc:
        yield tc


@pytest.fixture()
def failing_client(monkeypatch):
    monkeypatch.setattr(app_module, "_ocr_runtime", FailingOCRRuntime())
    monkeypatch.setattr(app_module, "_startup_error", None)
    with TestClient(app_module.app, raise_server_exceptions=False) as tc:
        yield tc


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_returns_200_when_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "device" in body
    assert "model_name" in body
    assert "model_version" in body


def test_health_returns_503_when_startup_failed(unhealthy_client):
    resp = unhealthy_client.get("/health")
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# POST /v1/ocr/recognize — valid image
# ---------------------------------------------------------------------------

def test_recognize_valid_image_returns_200(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    assert resp.status_code == 200


def test_recognize_response_has_required_top_level_fields(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    body = resp.json()
    for field in ("model_name", "model_version", "latency_ms", "quality", "lines"):
        assert field in body, f"Missing field: {field}"


def test_recognize_model_metadata_matches_config(client):
    from ml.app.config import settings
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    body = resp.json()
    assert body["model_name"] == settings.MODEL_NAME
    assert body["model_version"] == settings.MODEL_VERSION


def test_recognize_quality_fields_present(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    quality = resp.json()["quality"]
    for field in ("width", "height", "is_blank", "passed"):
        assert field in quality, f"Quality missing: {field}"


def test_recognize_line_has_calibrated_confidence_and_field_state(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    lines = resp.json()["lines"]
    assert len(lines) >= 1
    line = lines[0]
    assert "calibrated_confidence" in line
    assert "field_state" in line
    assert line["field_state"] in ("CLEAR", "AMBIGUOUS", "UNREADABLE", "NOT_PRESENT")


def test_recognize_line_has_extracted_fields(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    line = resp.json()["lines"][0]
    assert "extracted_fields" in line
    ef = line["extracted_fields"]
    for expected_key in ("name", "strength", "dose", "frequency", "duration"):
        assert expected_key in ef, f"extracted_fields missing: {expected_key}"


def test_recognize_latency_ms_is_non_negative(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    assert resp.json()["latency_ms"] >= 0


# ---------------------------------------------------------------------------
# POST /v1/ocr/recognize — blank image
# ---------------------------------------------------------------------------

def test_recognize_blank_image_quality_fails(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("blank.png", _make_blank_png(), "image/png")},
    )
    assert resp.status_code == 200
    quality = resp.json()["quality"]
    assert quality["is_blank"] is True
    assert quality["passed"] is False


# ---------------------------------------------------------------------------
# POST /v1/ocr/recognize — error paths
# ---------------------------------------------------------------------------

def test_recognize_non_image_file_returns_422(client):
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("doc.txt", b"This is not an image", "text/plain")},
    )
    assert resp.status_code == 422


def test_recognize_oversized_payload_returns_413(client, monkeypatch):
    from ml.app import config as cfg_module
    monkeypatch.setattr(cfg_module.settings, "MAX_UPLOAD_BYTES", 10)
    resp = client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    assert resp.status_code == 413


def test_recognize_malformed_multipart_returns_422(client):
    resp = client.post("/v1/ocr/recognize", data={"not_file": "bad"})
    assert resp.status_code == 422


def test_recognize_inference_failure_returns_422(failing_client):
    resp = failing_client.post(
        "/v1/ocr/recognize",
        files={"file": ("test.png", _make_png(), "image/png")},
    )
    assert resp.status_code == 422
