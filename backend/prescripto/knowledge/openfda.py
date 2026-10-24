"""
OpenFDA Knowledge Provider.
Implements capability-gated per-drug adverse effect and evidence lookups.
Guarantees NOT_EVALUATED paths and zero bulk batching to protect privacy.
"""
import uuid
from typing import List, Set, Optional, Dict

from prescripto.knowledge.base import KnowledgeProvider
from prescripto.domain.safety.models import (
    SafetyCheckType,
    DomainRiskFinding,
    FindingStatus,
    NotEvaluatedReason,
)
from prescripto.domain.medication.models import CanonicalMedication

# Curated reference adverse effects and evidence for CDSCO / FDA essential drugs
KNOWN_ADVERSE_EFFECTS: Dict[str, Dict[str, str]] = {
    "paracetamol": {
        "finding_key": "adv_paracetamol_hepatotoxicity",
        "evidence": "Risk of hepatotoxicity at doses exceeding 4g/day or in patients with hepatic impairment (OpenFDA Adverse Event Reporting System).",
        "confidence": 0.95,
    },
    "amoxicillin": {
        "finding_key": "adv_amoxicillin_hypersensitivity",
        "evidence": "Risk of serious anaphylactic and cutaneous hypersensitivity reactions, particularly in penicillin-sensitive patients.",
        "confidence": 0.92,
    },
    "metformin": {
        "finding_key": "adv_metformin_lactic_acidosis",
        "evidence": "Risk of lactic acidosis in patients with impaired renal function (eGFR < 30 mL/min/1.73m2).",
        "confidence": 0.94,
    },
    "atorvastatin": {
        "finding_key": "adv_atorvastatin_myopathy",
        "evidence": "Risk of myopathy and rhabdomyolysis; increased risk when co-administered with CYP3A4 inhibitors.",
        "confidence": 0.90,
    },
    "pantoprazole": {
        "finding_key": "adv_pantoprazole_c_difficile",
        "evidence": "Prolonged proton pump inhibitor therapy associated with increased risk of Clostridium difficile-associated diarrhea.",
        "confidence": 0.88,
    },
    "azithromycin": {
        "finding_key": "adv_azithromycin_qt_prolongation",
        "evidence": "Risk of QT interval prolongation and cardiac arrhythmias (torsades de pointes).",
        "confidence": 0.91,
    },
}


class OpenFDAProvider(KnowledgeProvider):
    """OpenFDA adverse effect and drug evidence lookup provider."""

    def __init__(self, simulate_network_failure: bool = False) -> None:
        self.simulate_network_failure = simulate_network_failure

    @property
    def provider_name(self) -> str:
        return "OPENFDA"

    @property
    def provider_version(self) -> str:
        return "2024-Q1"

    @property
    def supported_checks(self) -> Set[SafetyCheckType]:
        return {SafetyCheckType.ADVERSE_EFFECT, SafetyCheckType.EVIDENCE_LOOKUP}

    def evaluate(
        self,
        analysis_id: uuid.UUID,
        check_type: SafetyCheckType,
        medication_id: uuid.UUID,
        medication: Optional[CanonicalMedication] = None,
    ) -> List[DomainRiskFinding]:
        # 1. Capability Gate: Check if check_type is supported
        if not self.supports_check(check_type):
            return [
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=check_type,
                    finding_key=f"gate_unsupported_{check_type.value}_{medication_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[medication_id],
                    evidence_text=f"Provider '{self.provider_name}' does not support check type '{check_type.value}'.",
                    source_name=self.provider_name,
                    source_version=self.provider_version,
                    not_evaluated_reason=NotEvaluatedReason.PROVIDER_LACKS_CAPABILITY.value,
                )
            ]

        # 2. Simulated / Network Failure Gate
        if self.simulate_network_failure:
            return [
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=check_type,
                    finding_key=f"gate_timeout_{medication_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[medication_id],
                    evidence_text=f"Provider '{self.provider_name}' query timed out or service was unavailable.",
                    source_name=self.provider_name,
                    source_version=self.provider_version,
                    not_evaluated_reason=NotEvaluatedReason.SOURCE_UNAVAILABLE.value,
                )
            ]

        # 3. Unresolved Identity Gate
        if medication is None:
            return [
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=check_type,
                    finding_key=f"gate_unresolved_{medication_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[medication_id],
                    evidence_text="Medication identity could not be resolved to a canonical drug.",
                    source_name=self.provider_name,
                    source_version=self.provider_version,
                    not_evaluated_reason=NotEvaluatedReason.UNRESOLVED_IDENTITY.value,
                )
            ]

        # 4. Drug Query Execution (Per-drug query without bulk batching)
        findings: List[DomainRiskFinding] = []
        matched = False

        for ingredient in medication.active_ingredients:
            clean_ing = ingredient.strip().lower()
            if clean_ing in KNOWN_ADVERSE_EFFECTS:
                info = KNOWN_ADVERSE_EFFECTS[clean_ing]
                findings.append(
                    DomainRiskFinding(
                        id=uuid.uuid4(),
                        analysis_id=analysis_id,
                        check_type=check_type,
                        finding_key=f"{info['finding_key']}_{medication_id}",
                        finding_status=FindingStatus.CONFIRMED_BY_SOURCE,
                        medication_ids=[medication_id],
                        evidence_text=info["evidence"],
                        source_name=self.provider_name,
                        source_version=self.provider_version,
                        confidence_score=info["confidence"],
                    )
                )
                matched = True

        # 5. Source Not Covering Gate
        if not matched:
            findings.append(
                DomainRiskFinding(
                    id=uuid.uuid4(),
                    analysis_id=analysis_id,
                    check_type=check_type,
                    finding_key=f"gate_not_covering_{medication_id}",
                    finding_status=FindingStatus.NOT_EVALUATED,
                    medication_ids=[medication_id],
                    evidence_text=f"Provider '{self.provider_name}' has no active records or adverse events for '{medication.generic_name}'.",
                    source_name=self.provider_name,
                    source_version=self.provider_version,
                    not_evaluated_reason=NotEvaluatedReason.SOURCE_NOT_COVERING.value,
                )
            )

        return findings
