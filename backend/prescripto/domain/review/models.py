"""
Pure Domain Clinical Review Models and Routing Evaluation.
Zero external framework dependencies.
"""
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from prescripto.domain.analysis.models import AnalysisStatus
from prescripto.domain.safety.models import FindingStatus, DomainRiskFinding
from prescripto.domain.medication.models import ResolutionStatus

MANDATORY_COVERAGE_DISCLAIMER = (
    "Prescripto AI decision support is an assistive tool and does not constitute medical advice. "
    "Absence of detected risks does not guarantee safety. Review by an authorized medical professional is required."
)


class ReviewAction(str, Enum):
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    ESCALATED = "ESCALATED"


class ReviewStatus(str, Enum):
    PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ESCALATED = "ESCALATED"


@dataclass
class ReviewTriggerEvaluation:
    """Outcome of evaluating clinical review triggers across an analysis."""
    review_required: bool
    review_reasons: List[str]
    final_status: AnalysisStatus


def evaluate_review_triggers(
    medications: List[Dict[str, Any]],
    findings: List[DomainRiskFinding],
    quality_failed: bool = False,
) -> ReviewTriggerEvaluation:
    """
    Evaluates canonical review routing triggers according to PROJECT-SPEC and PRD:
    - Any field with 'AMBIGUOUS' state
    - Any medication with 'UNRESOLVED' or 'AMBIGUOUS' resolution status
    - Any risk finding with 'REQUIRES_REVIEW' or 'POTENTIAL'
    - Quality check failure (e.g. QUALITY_TOO_LOW)
    """
    reasons: List[str] = []

    if quality_failed:
        reasons.append("QUALITY_TOO_LOW: Document scan quality triggered human review threshold.")

    # 1. Medication line & field state triggers
    for med in medications:
        res_status = med.get("resolution_status")
        if res_status == ResolutionStatus.UNRESOLVED.value:
            reasons.append(f"UNRESOLVED_MEDICATION: Line {med.get('line_index', '?')} could not be normalized.")
        elif res_status == ResolutionStatus.AMBIGUOUS.value:
            reasons.append(f"AMBIGUOUS_MEDICATION: Line {med.get('line_index', '?')} has multiple competing candidates.")

        # Check field states: name, strength, dose, unit, frequency, route, duration, instructions
        for field_name in ["name", "strength", "dose", "unit", "frequency", "route", "duration", "instructions"]:
            field_data = med.get(field_name) or {}
            if isinstance(field_data, dict):
                state = field_data.get("state")
                if state == "AMBIGUOUS":
                    reasons.append(f"AMBIGUOUS_FIELD: Field '{field_name}' in medication line {med.get('line_index', '?')} is ambiguous.")
                elif state == "UNREADABLE":
                    reasons.append(f"UNREADABLE_FIELD: Field '{field_name}' in medication line {med.get('line_index', '?')} is unreadable.")

    # 2. Risk finding triggers
    for f in findings:
        if f.finding_status == FindingStatus.REQUIRES_REVIEW:
            reasons.append(f"FINDING_REQUIRES_REVIEW: Safety finding '{f.finding_key}' requires clinical evaluation.")
        elif f.finding_status == FindingStatus.POTENTIAL:
            reasons.append(f"POTENTIAL_RISK: Safety finding '{f.finding_key}' detected potential adverse condition.")

    review_required = len(reasons) > 0
    final_status = AnalysisStatus.REQUIRES_REVIEW if review_required else AnalysisStatus.COMPLETED

    return ReviewTriggerEvaluation(
        review_required=review_required,
        review_reasons=reasons,
        final_status=final_status,
    )
