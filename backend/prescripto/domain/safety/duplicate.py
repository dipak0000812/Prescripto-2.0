"""
Pure Domain Duplicate Medication Detector.
Zero external framework dependencies or external I/O.
Performs deterministic duplicate therapy and active ingredient overlap detection.
"""
import uuid
from typing import List, Set, Tuple
from prescripto.domain.safety.models import (
    DomainRiskFinding,
    SafetyCheckType,
    FindingStatus,
    NotEvaluatedReason,
)
from prescripto.domain.medication.models import CanonicalMedication, ResolutionStatus, MedicationResolutionResult


def detect_duplicate_medications(
    analysis_id: uuid.UUID,
    resolved_lines: List[Tuple[uuid.UUID, MedicationResolutionResult]],
) -> List[DomainRiskFinding]:
    """
    Flags repeated instances of the same canonical medication identity for reviewer attention.
    Each item in resolved_lines is a tuple of (prescription_medication_id, MedicationResolutionResult).

    - If a line is UNRESOLVED or AMBIGUOUS, generates a NOT_EVALUATED finding with appropriate reason.
    - Different products with a shared ingredient are not treated as the same prescribed product.
    - An identical canonical medication on multiple lines produces a POTENTIAL candidate, not a clinical conclusion.
    """
    findings: List[DomainRiskFinding] = []

    # 1. First pass: Handle unresolved / ambiguous lines with NOT_EVALUATED guarantee
    for line_id, res in resolved_lines:
        if res.resolution_status == ResolutionStatus.UNRESOLVED:
            findings.append(
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=SafetyCheckType.DUPLICATE_MEDICATION,
                    finding_key=f"not_eval_unresolved_{line_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[line_id],
                    evidence_text=f"Safety check for medication '{res.extracted_text}' could not be performed due to unresolved identity.",
                    source_name="PRESCRIPTO_DETERMINISTIC_RULES",
                    source_version="1.0.0",
                    not_evaluated_reason=NotEvaluatedReason.UNRESOLVED_IDENTITY.value,
                    confidence_score=None,
                )
            )
        elif res.resolution_status == ResolutionStatus.AMBIGUOUS:
            findings.append(
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=SafetyCheckType.DUPLICATE_MEDICATION,
                    finding_key=f"not_eval_ambiguous_{line_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[line_id],
                    evidence_text=f"Safety check for medication '{res.extracted_text}' could not be performed due to ambiguous identity.",
                    source_name="PRESCRIPTO_DETERMINISTIC_RULES",
                    source_version="1.0.0",
                    not_evaluated_reason=NotEvaluatedReason.AMBIGUOUS_IDENTITY.value,
                    confidence_score=None,
                )
            )

    # 2. Compare only exact canonical identities; ingredient overlap is not enough.
    resolved_items = [
        (line_id, res.resolved_medication)
        for line_id, res in resolved_lines
        if res.resolution_status == ResolutionStatus.RESOLVED and res.resolved_medication is not None
    ]

    seen_pairs: Set[Tuple[str, str]] = set()

    for i in range(len(resolved_items)):
        for j in range(i + 1, len(resolved_items)):
            id1, med1 = resolved_items[i]
            id2, med2 = resolved_items[j]

            pair_key = tuple(sorted([str(id1), str(id2)]))
            if pair_key in seen_pairs:
                continue

            if med1.id == med2.id:
                seen_pairs.add(pair_key)
                finding_key = f"dup_med_{pair_key[0]}_{pair_key[1]}"
                findings.append(
                    DomainRiskFinding(
                        id=uuid.uuid4(),
                        analysis_id=analysis_id,
                        check_type=SafetyCheckType.DUPLICATE_MEDICATION,
                        finding_key=finding_key,
                        finding_status=FindingStatus.POTENTIAL,
                        medication_ids=[id1, id2],
                        evidence_text="The same canonical product identity appears on multiple prescription lines; reviewer confirmation is required.",
                        source_name="PRESCRIPTO_DETERMINISTIC_RULES",
                        source_version="1.0.0",
                        confidence_score=None,
                    )
                )

    return findings
