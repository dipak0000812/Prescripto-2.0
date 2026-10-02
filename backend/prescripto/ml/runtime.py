"""
Model Runtime Abstraction.
Strictly implements docs/Architecture.md §11 ModelRuntime interface.
Isolates perception models (TrOCR, PP-OCRv6) behind a clean abstraction.
"""
from abc import ABC, abstractmethod
import time
import uuid
from typing import List, Optional

from prescripto.ml.models import (
    BoundingBox,
    RawRecognitionResult,
    CalibratedInferenceResult,
)
from prescripto.ml.calibration import TemperatureScalingCalibrator
from prescripto.domain.uncertainty.models import FieldState


class ModelRuntime(ABC):
    """
    Abstract Model Runtime Interface isolating perception model execution.
    Startup gates validate: registered version, calibration snapshot, and checkpoint sha256.
    """

    @abstractmethod
    def load(self, checkpoint_path: str) -> None:
        """Loads model weights and validates checkpoint integrity."""
        pass

    @abstractmethod
    def detect_regions(self, image_bytes: bytes) -> List[BoundingBox]:
        """Runs text detector (PP-OCRv6 / DBNet) returning line bounding boxes."""
        pass

    @abstractmethod
    def recognize_line(self, crop_bytes: bytes) -> RawRecognitionResult:
        """Runs text recognition (TrOCR / PP-OCRv6) on an individual line crop."""
        pass

    @property
    @abstractmethod
    def model_version_id(self) -> uuid.UUID:
        """Canonical model_versions.id pinned to this runtime."""
        pass

    @abstractmethod
    def run_calibrated_inference(
        self, crop_bytes: bytes, ground_truth_text: Optional[str] = None
    ) -> CalibratedInferenceResult:
        """Executes recognition and calibration, producing CalibratedInferenceResult."""
        pass


class MockModelRuntime(ModelRuntime):
    """
    High-fidelity development and test runtime conforming to ModelRuntime.
    Allows zero-dependency execution and testing of the end-to-end ML pipeline.
    """

    def __init__(
        self,
        model_version_id: Optional[uuid.UUID] = None,
        calibrator: Optional[TemperatureScalingCalibrator] = None,
    ) -> None:
        self._model_version_id = model_version_id or uuid.uuid4()
        self.calibrator = calibrator or TemperatureScalingCalibrator(temperature=1.0, review_threshold=0.85)
        self.is_loaded = True

    @property
    def model_version_id(self) -> uuid.UUID:
        return self._model_version_id

    def load(self, checkpoint_path: str) -> None:
        self.is_loaded = True

    def detect_regions(self, image_bytes: bytes) -> List[BoundingBox]:
        """Simulates bounding box detection on input document."""
        return [
            BoundingBox(x_min=50.0, y_min=100.0, x_max=450.0, y_max=140.0, label="line_0"),
            BoundingBox(x_min=50.0, y_min=160.0, x_max=450.0, y_max=200.0, label="line_1"),
        ]

    def recognize_line(self, crop_bytes: bytes) -> RawRecognitionResult:
        """Simulates line recognition."""
        return RawRecognitionResult(
            text="Augmentin 625 Duo 1 tab BD after food 5 days",
            raw_score=0.96,
            tokens=["Augmentin", "625", "Duo", "1", "tab", "BD", "after", "food", "5", "days"],
            token_confidences=[0.98, 0.97, 0.95, 0.99, 0.99, 0.94, 0.96, 0.95, 0.98, 0.97],
        )

    def run_calibrated_inference(
        self, crop_bytes: bytes, ground_truth_text: Optional[str] = None
    ) -> CalibratedInferenceResult:
        start_time = time.time()
        raw = self.recognize_line(crop_bytes)
        text = ground_truth_text if ground_truth_text is not None else raw.text
        calibrated_conf = self.calibrator.calibrate(raw.raw_score)
        state = self.calibrator.determine_state(calibrated_conf)
        latency_ms = int((time.time() - start_time) * 1000)

        return CalibratedInferenceResult(
            text=text,
            raw_score=raw.raw_score,
            calibrated_confidence=calibrated_conf,
            field_state=state,
            model_version_id=self.model_version_id,
            latency_ms=latency_ms,
        )
