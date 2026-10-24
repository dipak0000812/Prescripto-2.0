"""
Machine Learning Perception Domain Models.
Strictly conforms to docs/Architecture.md §11 and docs/ML-ARCHITECTURE.md.
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from prescripto.domain.uncertainty.models import FieldState


@dataclass(frozen=True)
class BoundingBox:
    """Represents a detected text region / line on a prescription document."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    polygon: Optional[List[Tuple[float, float]]] = None
    confidence: float = 1.0
    label: str = "line"


@dataclass(frozen=True)
class RawRecognitionResult:
    """Model-native recognition output from OCR recognizer (TrOCR / PP-OCR)."""
    text: str
    raw_score: float
    tokens: List[str] = field(default_factory=list)
    token_confidences: List[float] = field(default_factory=list)


@dataclass(frozen=True)
class CalibratedInferenceResult:
    """Post-calibration inference result with statistically grounded confidence and FieldState."""
    text: str
    raw_score: float
    calibrated_confidence: float
    field_state: FieldState
    model_version_id: uuid.UUID
    latency_ms: int
