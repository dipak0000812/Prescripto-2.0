"""
Pure Domain Medication and Normalization Models.
Zero external framework dependencies (no FastAPI, no SQLAlchemy, no Boto3).
"""
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


class MatchingStrategy(str, Enum):
    EXACT = "EXACT"
    FUZZY_SIMILARITY = "FUZZY_SIMILARITY"
    FTS_FULLTEXT = "FTS_FULLTEXT"


class SourceClass(str, Enum):
    CDSCO_REGULATORY = "CDSCO_REGULATORY"
    RXNORM = "RXNORM"
    MANUFACTURER_VERIFIED = "MANUFACTURER_VERIFIED"
    RESEARCH_VOCABULARY = "RESEARCH_VOCABULARY"
    MANUAL_EXPERT = "MANUAL_EXPERT"


class VerificationStatus(str, Enum):
    VERIFIED_AUTHORITY = "VERIFIED_AUTHORITY"
    PROVISIONAL = "PROVISIONAL"
    EXPERT_CONFIRMED = "EXPERT_CONFIRMED"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class CanonicalMedication:
    """Immutable domain representation of a Medication Master item."""
    id: uuid.UUID
    brand_name: str
    generic_name: str
    active_ingredients: List[str]
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    route: Optional[str] = None
    rxnorm_cui: Optional[str] = None
    source_class: str = SourceClass.CDSCO_REGULATORY.value
    source_version: str = "2024.1"
    verification_status: str = VerificationStatus.VERIFIED_AUTHORITY.value
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateMatch:
    """Represents a scored candidate for medication normalization."""
    medication: CanonicalMedication
    candidate_score: float
    matching_strategy: str
    source_vocabulary: str = "CDSCO"


@dataclass
class MedicationResolutionResult:
    """Result of normalizing an extracted medication string against Medication Master."""
    extracted_text: str
    resolution_status: ResolutionStatus
    resolved_medication: Optional[CanonicalMedication] = None
    candidates: List[CandidateMatch] = field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        return self.resolution_status == ResolutionStatus.RESOLVED

    @property
    def is_ambiguous(self) -> bool:
        return self.resolution_status == ResolutionStatus.AMBIGUOUS


def resolve_candidate_matches(
    extracted_text: str,
    candidates: List[CandidateMatch],
    resolution_threshold: float = 0.85,
    ambiguity_margin: float = 0.10,
) -> MedicationResolutionResult:
    """
    Pure domain resolution decision:
    - Sorts candidates descending by score.
    - If best candidate >= resolution_threshold and:
        - only 1 candidate, or
        - top candidate score - 2nd candidate score >= ambiguity_margin:
        -> RESOLVED
    - If top candidate >= 0.70 but 2nd candidate is within ambiguity_margin:
        -> AMBIGUOUS
    - If no candidate >= 0.70:
        -> UNRESOLVED
    """
    if not candidates:
        return MedicationResolutionResult(
            extracted_text=extracted_text,
            resolution_status=ResolutionStatus.UNRESOLVED,
            resolved_medication=None,
            candidates=[],
        )

    sorted_candidates = sorted(candidates, key=lambda c: c.candidate_score, reverse=True)
    top = sorted_candidates[0]

    if top.candidate_score >= resolution_threshold:
        if len(sorted_candidates) == 1:
            return MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=ResolutionStatus.RESOLVED,
                resolved_medication=top.medication,
                candidates=sorted_candidates,
            )
        second = sorted_candidates[1]
        if (top.candidate_score - second.candidate_score) >= ambiguity_margin:
            return MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=ResolutionStatus.RESOLVED,
                resolved_medication=top.medication,
                candidates=sorted_candidates,
            )
        else:
            return MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=ResolutionStatus.AMBIGUOUS,
                resolved_medication=None,
                candidates=sorted_candidates,
            )

    if top.candidate_score >= 0.70 and len(sorted_candidates) > 1:
        second = sorted_candidates[1]
        if (top.candidate_score - second.candidate_score) < ambiguity_margin:
            return MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=ResolutionStatus.AMBIGUOUS,
                resolved_medication=None,
                candidates=sorted_candidates,
            )

    return MedicationResolutionResult(
        extracted_text=extracted_text,
        resolution_status=ResolutionStatus.UNRESOLVED,
        resolved_medication=None,
        candidates=sorted_candidates,
    )
