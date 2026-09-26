"""
Unit tests for Pure Domain Safety Engine & Duplicate Medication Detector.
"""
import uuid
import pytest
from prescripto.domain.safety.models import (
    SafetyCheckType,
    FindingStatus,
    NotEvaluatedReason,
    DomainRiskFinding,
    MissingNotEvaluatedReasonException,
)
from prescripto.domain.safety.duplicate import detect_duplicate_medications
from prescripto.domain.medication.models import (
    CanonicalMedication,
    MedicationResolutionResult,
    ResolutionStatus,
)


def test_domain_risk_finding_not_evaluated_invariant():
    # 1. Invariant: NOT_EVALUATED requires not_evaluated_reason
    with pytest.raises(MissingNotEvaluatedReasonException):
        DomainRiskFinding(
            id=uuid.uuid4(),
            analysis_id=uuid.uuid4(),
            check_type=SafetyCheckType.DUPLICATE_MEDICATION,
            finding_key="test_key",
            finding_status=FindingStatus.NOT_EVALUATED,
            medication_ids=[uuid.uuid4()],
            evidence_text=None,
            source_name="TEST",
            source_version="1.0",
            not_evaluated_reason=None,  # Violates invariant
        )

    # 2. Valid NOT_EVALUATED finding with reason
    finding = DomainRiskFinding(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        check_type=SafetyCheckType.DUPLICATE_MEDICATION,
        finding_key="test_key",
        finding_status=FindingStatus.NOT_EVALUATED,
        medication_ids=[uuid.uuid4()],
        evidence_text=None,
        source_name="TEST",
        source_version="1.0",
        not_evaluated_reason=NotEvaluatedReason.PROVIDER_LACKS_CAPABILITY.value,
    )
    assert finding.finding_status == FindingStatus.NOT_EVALUATED
    assert finding.not_evaluated_reason == "PROVIDER_LACKS_CAPABILITY"


def test_domain_risk_finding_confidence_bounds():
    with pytest.raises(ValueError):
        DomainRiskFinding(
            id=uuid.uuid4(),
            analysis_id=uuid.uuid4(),
            check_type=SafetyCheckType.DUPLICATE_MEDICATION,
            finding_key="test_key",
            finding_status=FindingStatus.CONFIRMED_BY_SOURCE,
            medication_ids=[uuid.uuid4()],
            evidence_text="test",
            source_name="TEST",
            source_version="1.0",
            confidence_score=1.5,  # Out of bounds
        )


def test_detect_duplicate_medications_overlapping_active_ingredients():
    analysis_id = uuid.uuid4()
    line1_id = uuid.uuid4()
    line2_id = uuid.uuid4()

    med1 = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol 650",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        strength="650mg",
    )
    med2 = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Dolo 650",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        strength="650mg",
    )

    resolved_lines = [
        (line1_id, MedicationResolutionResult(extracted_text="Calpol", resolution_status=ResolutionStatus.RESOLVED, resolved_medication=med1)),
        (line2_id, MedicationResolutionResult(extracted_text="Dolo", resolution_status=ResolutionStatus.RESOLVED, resolved_medication=med2)),
    ]

    findings = detect_duplicate_medications(analysis_id, resolved_lines)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_type == SafetyCheckType.DUPLICATE_MEDICATION
    assert f.finding_status == FindingStatus.CONFIRMED_BY_SOURCE
    assert set(f.medication_ids) == {line1_id, line2_id}
    assert "Paracetamol" in f.evidence_text


def test_detect_duplicate_medications_unresolved_guarantee():
    analysis_id = uuid.uuid4()
    line1_id = uuid.uuid4()

    resolved_lines = [
        (line1_id, MedicationResolutionResult(extracted_text="UnknownDrugXYZ", resolution_status=ResolutionStatus.UNRESOLVED, resolved_medication=None)),
    ]

    findings = detect_duplicate_medications(analysis_id, resolved_lines)
    assert len(findings) == 1
    assert findings[0].finding_status == FindingStatus.NOT_EVALUATED
    assert findings[0].not_evaluated_reason == NotEvaluatedReason.UNRESOLVED_IDENTITY.value
