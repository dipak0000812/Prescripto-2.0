"""
Unit tests for ML Perception, Calibration, and ModelRuntime.
"""
import uuid
from prescripto.ml.models import BoundingBox, RawRecognitionResult, CalibratedInferenceResult
from prescripto.ml.calibration import TemperatureScalingCalibrator
from prescripto.ml.runtime import MockModelRuntime, RemoteMLClient
from prescripto.domain.uncertainty.models import FieldState
import pytest
from unittest.mock import MagicMock, patch
import httpx


def test_temperature_scaling_calibrator_clear():
    calibrator = TemperatureScalingCalibrator(temperature=1.0, review_threshold=0.85, illegibility_floor=0.30)
    conf = calibrator.calibrate(0.95)
    assert 0.90 <= conf <= 1.0
    state = calibrator.determine_state(conf)
    assert state == FieldState.CLEAR


def test_temperature_scaling_calibrator_ambiguous():
    calibrator = TemperatureScalingCalibrator(temperature=1.0, review_threshold=0.85, illegibility_floor=0.30)
    conf = calibrator.calibrate(0.70)
    assert 0.60 <= conf <= 0.84
    state = calibrator.determine_state(conf)
    assert state == FieldState.AMBIGUOUS


def test_temperature_scaling_calibrator_unreadable():
    calibrator = TemperatureScalingCalibrator(temperature=1.0, review_threshold=0.85, illegibility_floor=0.30)
    conf = calibrator.calibrate(0.10)
    assert conf < 0.30
    state = calibrator.determine_state(conf)
    assert state == FieldState.UNREADABLE


def test_mock_model_runtime_detect_and_recognize():
    model_id = uuid.uuid4()
    runtime = MockModelRuntime(model_version_id=model_id)

    # 1. Detection
    dummy_image = b"dummy_image_data"
    boxes = runtime.detect_regions(dummy_image)
    assert len(boxes) == 2
    assert isinstance(boxes[0], BoundingBox)
    assert boxes[0].x_min < boxes[0].x_max

    # 2. Recognition
    raw = runtime.recognize_line(b"crop")
    assert isinstance(raw, RawRecognitionResult)
    assert "Augmentin" in raw.text
    assert raw.raw_score > 0.90

    # 3. Calibrated inference
    calibrated = runtime.run_calibrated_inference(b"crop")
    assert isinstance(calibrated, CalibratedInferenceResult)
    assert calibrated.field_state == FieldState.CLEAR
    assert calibrated.model_version_id == model_id


def test_remote_ml_client_success():
    client = RemoteMLClient(ml_service_url="http://ml-test:8001")
    fake_response_data = {
        "model_name": "PP-OCRv6",
        "model_version": "6.0.0",
        "latency_ms": 42,
        "quality": {"width": 800, "height": 600, "is_blank": False, "passed": True},
        "lines": [
            {
                "line_index": 0,
                "text": "Paracetamol 500mg TDS",
                "raw_score": 0.98,
                "calibrated_confidence": 0.98,
                "field_state": "CLEAR",
                "box": [10.0, 20.0, 300.0, 50.0],
                "extracted_fields": {},
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_response_data

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        lines = client.recognize_document(b"fake_image_bytes")
        mock_post.assert_called_once()
        assert len(lines) == 1
        assert lines[0].line_index == 0
        assert lines[0].text == "Paracetamol 500mg TDS"
        assert lines[0].raw_score == 0.98
        assert lines[0].box == (10.0, 20.0, 300.0, 50.0)


def test_remote_ml_client_http_error():
    client = RemoteMLClient(ml_service_url="http://ml-test:8001")
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("httpx.post", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="ML service returned HTTP 500"):
            client.recognize_document(b"fake_image_bytes")


def test_remote_ml_client_network_error():
    client = RemoteMLClient(ml_service_url="http://ml-test:8001")
    with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(RuntimeError, match="ML service request failed"):
            client.recognize_document(b"fake_image_bytes")

