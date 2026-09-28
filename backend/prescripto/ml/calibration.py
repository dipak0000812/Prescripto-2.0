"""
Confidence Calibration Engine.
Converts model-native scores (TrOCR beam-search, PP-OCR CTC) into calibrated probabilities.
Buckets calibrated confidence against model version review thresholds into FieldState.
"""
import math
from typing import Dict, Any, Optional
from prescripto.domain.uncertainty.models import FieldState


class TemperatureScalingCalibrator:
    """
    Applies temperature scaling: calibrated_p = 1 / (1 + exp(-logit / T))
    and buckets against review_threshold and illegibility floor.
    """

    def __init__(
        self,
        temperature: float = 1.0,
        review_threshold: float = 0.85,
        illegibility_floor: float = 0.30,
    ) -> None:
        self.temperature = max(0.01, temperature)
        self.review_threshold = review_threshold
        self.illegibility_floor = illegibility_floor

    def calibrate(self, raw_score: float) -> float:
        """Scales raw probability or score into calibrated probability [0.0, 1.0]."""
        raw_clamped = max(0.001, min(0.999, raw_score))
        logit = math.log(raw_clamped / (1.0 - raw_clamped))
        scaled_logit = logit / self.temperature
        calibrated = 1.0 / (1.0 + math.exp(-scaled_logit))
        return round(max(0.0, min(1.0, calibrated)), 4)

    def determine_state(self, calibrated_confidence: float) -> FieldState:
        """Buckets confidence against thresholds."""
        if calibrated_confidence < self.illegibility_floor:
            return FieldState.UNREADABLE
        elif calibrated_confidence < self.review_threshold:
            return FieldState.AMBIGUOUS
        else:
            return FieldState.CLEAR
