"""
Pure Domain Safety Models and Invariants.
Zero external framework dependencies (no FastAPI, no SQLAlchemy, no Boto3).
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class SafetyCheckType(str, Enum):
    DUPLICATE_MEDICATION = "DUPLICATE_MEDICATION"
    EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"
    ADVERSE_EFFECT = "ADVERSE_EFFECT"
    # Note: KNOWN_INTERACTION and DOSAGE_RANGE are deferred in V1 (ADR-08)


class FindingStatus(str, Enum):
    CONFIRMED_BY_SOURCE = "CONFIRMED_BY_SOURCE"
    POTENTIAL = "POTENTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_EVALUATED = "NOT_EVALUATED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class NotEvaluatedReason(str, Enum):
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    PROVIDER_LACKS_CAPABILITY = "PROVIDER_LACKS_CAPABILITY"
    UNRESOLVED_IDENTITY = "UNRESOLVED_IDENTITY"
    AMBIGUOUS_IDENTITY = "AMBIGUOUS_IDENTITY"
    SOURCE_NOT_COVERING = "SOURCE_NOT_COVERING"
    CHECK_TYPE_DEFERRED = "CHECK_TYPE_DEFERRED"
    LICENSE_MODE_EXCLUDED = "LICENSE_MODE_EXCLUDED"


class SafetyDomainException(Exception):
    """Base domain exception for safety engine invariant violations."""
    pass


class MissingNotEvaluatedReasonException(SafetyDomainException):
    """Raised when a finding with status NOT_EVALUATED is created without a reason."""
    def __init__(self, message: str = "A finding with NOT_EVALUATED status must specify not_evaluated_reason"):
        super().__init__(message)


@dataclass(frozen=True)
class DomainRiskFinding:
    """
    Pure domain representation of a safety risk finding.
    Strictly enforces DB check constraint chk_not_evaluated_reason:
    finding_status != 'NOT_EVALUATED' OR not_evaluated_reason IS NOT NULL.
    """
    id: uuid.UUID
    analysis_id: uuid.UUID
    check_type: SafetyCheckType
    finding_key: str
    finding_status: FindingStatus
    medication_ids: List[uuid.UUID]
    evidence_text: Optional[str]
    source_name: str
    source_version: str
    knowledge_snapshot_id: Optional[uuid.UUID] = None
    confidence_score: Optional[float] = None
    check_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    not_evaluated_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.finding_status == FindingStatus.NOT_EVALUATED and not self.not_evaluated_reason:
            raise MissingNotEvaluatedReasonException()
        if self.confidence_score is not None and not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"Confidence score must be in [0.0, 1.0], got {self.confidence_score}")
