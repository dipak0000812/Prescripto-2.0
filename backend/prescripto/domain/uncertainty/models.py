"""
Pure Domain Uncertainty Type System.
Strict Layering: Zero external dependencies (no FastAPI, no SQLAlchemy, no Boto3).
Implements the Uncertainty Invariant: Upstream uncertainty must never silently become downstream certainty.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class FieldState(str, Enum):
    CLEAR = "CLEAR"              # High confidence, above calibrated threshold
    AMBIGUOUS = "AMBIGUOUS"      # Low confidence or conflicting candidates -> routes to review
    UNREADABLE = "UNREADABLE"    # Illegible text -> structurally excluded from downstream stages
    NOT_PRESENT = "NOT_PRESENT"  # Field absent from document


class UncertaintyPropagationError(Exception):
    """Raised when an UNREADABLE field illegally attempts to propagate to downstream stages."""
    pass


@dataclass(frozen=True)
class ExtractedField(Generic[T]):
    """
    Type-safe extracted field with calibrated uncertainty tracking.
    Enforces the invariant:
    - UNREADABLE fields trigger an immediate domain error if propagated.
    - Non-CLEAR fields propagate as AMBIGUOUS to prevent false confidence.
    """
    value: Optional[T]
    state: FieldState
    confidence: float
    raw_text: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence score must be in [0.0, 1.0], got {self.confidence}")

    def propagate(self) -> "ExtractedField[T]":
        """
        Propagates uncertainty to downstream stages:
        - Raises UncertaintyPropagationError if UNREADABLE.
        - Preserves CLEAR state.
        - Buckets any non-CLEAR state into AMBIGUOUS.
        """
        if self.state == FieldState.UNREADABLE:
            raise UncertaintyPropagationError(
                f"UNREADABLE field '{self.raw_text}' must not reach normalization or safety stages."
            )
        if self.state == FieldState.NOT_PRESENT:
            return self
        if self.state != FieldState.CLEAR:
            return ExtractedField(
                value=self.value,
                state=FieldState.AMBIGUOUS,
                confidence=self.confidence,
                raw_text=self.raw_text,
            )
        return self
