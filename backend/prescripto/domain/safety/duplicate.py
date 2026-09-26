"""
Pure Domain Duplicate Medication Detector.
Zero external framework dependencies or external I/O.
Performs deterministic duplicate therapy and active ingredient overlap detection.
"""
import uuid
from typing import List, Dict, Set, Tuple
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
    Analyzes normalized prescription medication lines for duplicate active ingredients or brand therapies.
    Each item in resolved_lines is a tuple of (prescription_medication_id, MedicationResolutionResult).

    - If a line is UNRESOLVED or AMBIGUOUS, generates a NOT_EVALUATED finding with appropriate reason.
    - If multiple lines share active ingredient(s) or canonical drug identity, generates DUPLICATE_MEDICATION finding.
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

    # 2. Second pass: Pairwise duplicate active ingredients and identity checks for resolved lines
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

            # Compare active ingredients (normalized lowercase)
            ing1 = {ing.strip().lower() for ing in med1.active_ingredients if ing.strip()}
            ing2 = {ing.strip().lower() for ing in med2.active_ingredients if ing.strip()}

            overlapping = ing1.intersection(ing2)
            same_drug = med1.id == med2.id or (
                med1.generic_name.strip().lower() == med2.generic_name.strip().lower()
                and med1.brand_name.strip().lower() == med2.brand_name.strip().lower()
            )

            if overlapping or same_drug:
                seen_pairs.add(pair_key)
                if overlapping:
                    overlap_str = ", ".join(sorted(overlapping))
                    evidence = (
                        f"Duplicate active ingredient(s) [{overlap_str}] detected between "
                        f"'{med1.brand_name}' ({med1.generic_name}) and '{med2.brand_name}' ({med2.generic_name})."
                    )
                else:
                    evidence = (
                        f"Duplicate medication prescribed: '{med1.brand_name}' ({med1.generic_name}) appears multiple times."
                    )

                finding_key = f"dup_med_{pair_key[0]}_{pair_key[1]}"
                findings.append(
                    DomainRiskFinding(
                        id=uuid.uuid4(),
                        analysis_id=analysis_id,
                        check_type=SafetyCheckType.DUPLICATE_MEDICATION,
                        finding_key=finding_key,
                        finding_status=FindingStatus.CONFIRMED_BY_SOURCE,
                        medication_ids=[id1, id2],
                        evidence_text=evidence,
                        source_name="PRESCRIPTO_DETERMINISTIC_RULES",
                        source_version="1.0.0",
                        confidence_score=1.0,
                    )
                )

    return findings
