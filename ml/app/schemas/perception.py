"""
ML Service — Perception Domain Models.

Verbatim copy of backend/prescripto/ml/models.py and the FieldState enum from
backend/prescripto/domain/uncertainty/models.py.

Import path changed from prescripto.* to self-contained ml.app.* so that the
ML service has zero dependency on the backend package.  Algorithm unchanged.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# FieldState — copied verbatim from backend/prescripto/domain/uncertainty/models.py
# The ML service owns these labels for its own inference output only.
# The backend's canonical copy remains in prescripto.domain.uncertainty.models.
# ---------------------------------------------------------------------------

class FieldState(str, Enum):
    CLEAR = "CLEAR"              # High confidence, above calibrated threshold
    AMBIGUOUS = "AMBIGUOUS"      # Low confidence or conflicting candidates → routes to review
    UNREADABLE = "UNREADABLE"    # Illegible text → structurally excluded from downstream stages
    NOT_PRESENT = "NOT_PRESENT"  # Field absent from document


# ---------------------------------------------------------------------------
# Perception data structures — verbatim from backend/prescripto/ml/models.py
# ---------------------------------------------------------------------------

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
    """Model-native recognition output from OCR recognizer (PP-OCR)."""
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
