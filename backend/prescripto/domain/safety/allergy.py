"""
Pure Domain Allergy Contraindication Detector.
Cross-references patient allergen records with extracted/canonical medications.
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


ALLERGY_CLASS_CROSS_REFERENCE: Dict[str, Set[str]] = {
    "penicillin": {
        "penicillin", "amoxicillin", "ampicillin", "augmentin", "piperacillin",
        "clavulanate", "oxacillin", "dicloxacillin", "amox", "moxclav", "ampiclox"
    },
    "sulfa": {
        "sulfa", "sulfonamide", "sulfamethoxazole", "bactrim", "septra",
        "cotrimoxazole", "sulfasalazine", "sulfadiazine", "trimethoprim-sulfamethoxazole"
    },
    "sulfonamide": {
        "sulfa", "sulfonamide", "sulfamethoxazole", "bactrim", "septra",
        "cotrimoxazole", "sulfasalazine", "sulfadiazine"
    },
    "nsaid": {
        "aspirin", "ibuprofen", "naproxen", "diclofenac", "ketorolac",
        "indomethacin", "celecoxib", "etoricoxib", "piroxicam", "mefenamic", "voveran"
    },
    "aspirin": {
        "aspirin", "acetylsalicylic", "ecospirin", "disprin", "nsaid"
    },
    "cephalosporin": {
        "cefixime", "ceftriaxone", "cefuroxime", "cephalexin", "cefotaxime",
        "cefepime", "cefadroxil", "taxim", "monocef"
    },
    "macrolide": {
        "azithromycin", "clarithromycin", "erythromycin", "roxithromycin", "azithral"
    },
    "fluoroquinolone": {
        "ciprofloxacin", "levofloxacin", "ofloxacin", "moxifloxacin", "norfloxacin", "ciplox"
    },
    "paracetamol": {
        "paracetamol", "acetaminophen", "calpol", "crocin", "dolo", "pacimol"
    },
    "acetaminophen": {
        "paracetamol", "acetaminophen", "calpol", "crocin", "dolo", "pacimol"
    },
    "statin": {
        "atorvastatin", "rosuvastatin", "simvastatin", "atorva", "rosuvas"
    },
}


def _extract_allergen_tokens(allergy_text: Optional[str]) -> List[str]:
    """Parse comma/semicolon/newline-separated patient allergies into clean tokens."""
    if not allergy_text:
        return []
    
    parts = re.split(r"[,;\n\r/]+", allergy_text)
    tokens: List[str] = []
    for part in parts:
        cleaned = part.strip().lower()
        # Remove common filler words
        cleaned = re.sub(r"\b(allergy|allergic|to|drugs?|sensitive|reaction)\b", "", cleaned).strip()
        if cleaned and len(cleaned) >= 2:
            tokens.append(cleaned)
    return tokens


def detect_allergy_contraindications(
    analysis_id: uuid.UUID,
    patient_allergies_str: Optional[str],
    medication_lines: List[Tuple[uuid.UUID, str, Optional[CanonicalMedication]]],
) -> List[DomainRiskFinding]:
    """
    Evaluates patient allergy history against prescribed medications.
    Each item in medication_lines: (line_id, raw_name, canonical_medication_or_None).
    """
    allergens = _extract_allergen_tokens(patient_allergies_str)
    if not allergens:
        return []

    findings: List[DomainRiskFinding] = []
    seen_keys: Set[str] = set()

    for line_id, raw_name, canonical in medication_lines:
        drug_names_to_check: List[str] = [raw_name.lower()]
        ingredients_to_check: List[str] = []

        if canonical:
            drug_names_to_check.append(canonical.brand_name.lower())
            drug_names_to_check.append(canonical.generic_name.lower())
            for ing in canonical.active_ingredients:
                ingredients_to_check.append(ing.lower())

        all_drug_strings = drug_names_to_check + ingredients_to_check

        for allergen in allergens:
            matched = False
            match_detail = ""

            # 1. Direct text match
            for text in all_drug_strings:
                if allergen in text or text in allergen:
                    matched = True
                    match_detail = f"Matched direct drug entity '{text}'"
                    break

            # 2. Cross-reference clinical class match
            if not matched:
                for class_key, class_members in ALLERGY_CLASS_CROSS_REFERENCE.items():
                    if allergen == class_key or allergen in class_key:
                        for text in all_drug_strings:
                            for member in class_members:
                                if member in text:
                                    matched = True
                                    match_detail = f"Cross-reactive class '{class_key}' via compound '{member}'"
                                    break
                            if matched:
                                break
                    if matched:
                        break

            if matched:
                finding_key = f"allergy_{line_id}_{re.sub(r'[^a-zA-Z0-9_]', '_', allergen)}"
                if finding_key not in seen_keys:
                    seen_keys.add(finding_key)
                    display_name = canonical.brand_name if canonical else raw_name
                    findings.append(
                        DomainRiskFinding(
                            id=uuid.uuid4(),
                            analysis_id=analysis_id,
                            check_type=SafetyCheckType.ADVERSE_EFFECT,
                            finding_key=finding_key,
                            finding_status=FindingStatus.CONFIRMED_BY_SOURCE,
                            medication_ids=[line_id],
                            evidence_text=(
                                f"CRITICAL ALLERGY CONTRAINDICATION: Patient record indicates sensitivity to '{allergen}'. "
                                f"Prescribed item '{display_name}' ({match_detail}) is contraindicated. "
                                "Physician sign-off is mandatory before dispensing."
                            ),
                            source_name="PRESCRIPTO_CLINICAL_SAFETY_ENGINE",
                            source_version="1.0.0",
                            confidence_score=0.98,
                        )
                    )

    return findings
