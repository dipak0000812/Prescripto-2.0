"""
Pure Domain Dosage Safety Range Evaluator.
Identifies potentially elevated single-dose or cumulative dosing regimens.
Zero external I/O or database dependencies.
"""
import re
import uuid
from typing import Dict, List, Optional, Set, Tuple
from prescripto.domain.safety.models import (
    DomainRiskFinding,
    SafetyCheckType,
    FindingStatus,
)
from prescripto.domain.medication.models import CanonicalMedication


DOSAGE_MAX_THRESHOLDS: Dict[str, float] = {
    # mg per single unit / dose
    "paracetamol": 1000.0,
    "acetaminophen": 1000.0,
    "calpol": 1000.0,
    "crocin": 1000.0,
    "dolo": 1000.0,
    "amoxicillin": 1000.0,
    "augmentin": 1000.0,
    "metformin": 1000.0,
    "azithromycin": 500.0,
    "ciprofloxacin": 750.0,
    "levofloxacin": 750.0,
    "pantoprazole": 80.0,
    "omeprazole": 40.0,
    "amlodipine": 10.0,
    "atorvastatin": 80.0,
    "ibuprofen": 800.0,
    "cetirizine": 20.0,
}


def _parse_mg_value(text: Optional[str]) -> Optional[float]:
    """Extract numeric milligrams from strength or dose string."""
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mg|milligram|mgs)\b", text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def detect_dosage_safety_warnings(
    analysis_id: uuid.UUID,
    medication_lines: List[Tuple[uuid.UUID, str, Optional[str], Optional[str], Optional[CanonicalMedication]]],
) -> List[DomainRiskFinding]:
    """
    Evaluates medication dose and strength against established therapeutic max limits.
    Each item: (line_id, raw_name, raw_strength, raw_dose, canonical_or_None).
    """
    findings: List[DomainRiskFinding] = []
    seen_keys: Set[str] = set()

    for line_id, raw_name, raw_strength, raw_dose, canonical in medication_lines:
        strength_mg = _parse_mg_value(raw_strength) or _parse_mg_value(raw_dose) or _parse_mg_value(raw_name)
        if not strength_mg:
            continue

        drug_candidates = [raw_name.lower()]
        if canonical:
            drug_candidates.append(canonical.brand_name.lower())
            drug_candidates.append(canonical.generic_name.lower())
            for ing in canonical.active_ingredients:
                drug_candidates.append(ing.lower())

        flagged_for_line = False
        for drug_term in drug_candidates:
            if flagged_for_line:
                break
            for drug_key, max_mg in DOSAGE_MAX_THRESHOLDS.items():
                if drug_key in drug_term:
                    if strength_mg > max_mg:
                        finding_key = f"dosage_high_{line_id}"
                        if finding_key not in seen_keys:
                            seen_keys.add(finding_key)
                            display_name = canonical.brand_name if canonical else raw_name
                            findings.append(
                                DomainRiskFinding(
                                    id=uuid.uuid4(),
                                    analysis_id=analysis_id,
                                    check_type=SafetyCheckType.ADVERSE_EFFECT,
                                    finding_key=finding_key,
                                    finding_status=FindingStatus.REQUIRES_REVIEW,
                                    medication_ids=[line_id],
                                    evidence_text=(
                                        f"DOSAGE SAFETY WARNING: Prescribed dose/strength '{strength_mg}mg' for '{display_name}' "
                                        f"exceeds standard single-dose reference limit ({max_mg}mg). "
                                        "Physician review is recommended to prevent adverse effects."
                                    ),
                                    source_name="PRESCRIPTO_DOSAGE_SAFETY_ENGINE",
                                    source_version="1.0.0",
                                    confidence_score=0.92,
                                )
                            )
                            flagged_for_line = True
                            break

    return findings
