"""
Unit tests for ML Perception, Calibration, and ModelRuntime.
"""
import uuid
from prescripto.ml.models import BoundingBox, RawRecognitionResult, CalibratedInferenceResult
from prescripto.ml.calibration import TemperatureScalingCalibrator
from prescripto.ml.runtime import MockModelRuntime
from prescripto.domain.uncertainty.models import FieldState


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
