"""
Unit tests for Medication Candidate Resolution and OpenFDA Knowledge Provider.
"""
import uuid
import pytest
from prescripto.domain.medication.models import (
    CanonicalMedication,
    CandidateMatch,
    MatchingStrategy,
    ResolutionStatus,
    resolve_candidate_matches,
)
from prescripto.domain.safety.models import SafetyCheckType, FindingStatus, NotEvaluatedReason
from prescripto.knowledge.openfda import OpenFDAProvider


def test_resolve_candidates_resolved_single_strong():
    med = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Augmentin 625 Duo",
        generic_name="Amoxicillin and Potassium Clavulanate",
        active_ingredients=["Amoxicillin", "Potassium Clavulanate"],
    )
    candidates = [
        CandidateMatch(medication=med, candidate_score=0.95, matching_strategy=MatchingStrategy.EXACT.value),
    ]
    result = resolve_candidate_matches("Augmentin", candidates)
    assert result.resolution_status == ResolutionStatus.RESOLVED
    assert result.resolved_medication == med


def test_resolve_candidates_ambiguous_two_close():
    med1 = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol 500",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
    )
    med2 = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol 650",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
    )
    candidates = [
        CandidateMatch(medication=med1, candidate_score=0.88, matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value),
        CandidateMatch(medication=med2, candidate_score=0.85, matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value),
    ]
    result = resolve_candidate_matches("Calpol", candidates, ambiguity_margin=0.05)
    assert result.resolution_status == ResolutionStatus.AMBIGUOUS
    assert result.resolved_medication is None


def test_resolve_candidates_unresolved_low_score():
    med = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Pantocid 40",
        generic_name="Pantoprazole",
        active_ingredients=["Pantoprazole"],
    )
    candidates = [
        CandidateMatch(medication=med, candidate_score=0.45, matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value),
    ]
    result = resolve_candidate_matches("CompletelyDifferent", candidates)
    assert result.resolution_status == ResolutionStatus.UNRESOLVED
    assert result.resolved_medication is None


def test_openfda_provider_capability_gate():
    provider = OpenFDAProvider()
    med_id = uuid.uuid4()
    analysis_id = uuid.uuid4()

    # KNOWN_INTERACTION is not in supported checks
    findings = provider.evaluate(
        analysis_id=analysis_id,
        check_type=SafetyCheckType.DUPLICATE_MEDICATION,
        medication_id=med_id,
    )
    assert len(findings) == 1
    assert findings[0].finding_status == FindingStatus.NOT_EVALUATED
    assert findings[0].not_evaluated_reason == NotEvaluatedReason.PROVIDER_LACKS_CAPABILITY.value


def test_openfda_provider_unresolved_gate():
    provider = OpenFDAProvider()
    findings = provider.evaluate(
        analysis_id=uuid.uuid4(),
        check_type=SafetyCheckType.ADVERSE_EFFECT,
        medication_id=uuid.uuid4(),
        medication=None,
    )
    assert len(findings) == 1
    assert findings[0].finding_status == FindingStatus.NOT_EVALUATED
    assert findings[0].not_evaluated_reason == NotEvaluatedReason.UNRESOLVED_IDENTITY.value


def test_openfda_provider_simulated_failure():
    provider = OpenFDAProvider(simulate_network_failure=True)
    findings = provider.evaluate(
        analysis_id=uuid.uuid4(),
        check_type=SafetyCheckType.ADVERSE_EFFECT,
        medication_id=uuid.uuid4(),
    )
    assert len(findings) == 1
    assert findings[0].finding_status == FindingStatus.NOT_EVALUATED
    assert findings[0].not_evaluated_reason == NotEvaluatedReason.SOURCE_UNAVAILABLE.value


def test_openfda_provider_evaluates_known_adverse_effect():
    provider = OpenFDAProvider()
    med = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol 650",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
    )
    findings = provider.evaluate(
        analysis_id=uuid.uuid4(),
        check_type=SafetyCheckType.ADVERSE_EFFECT,
        medication_id=med.id,
        medication=med,
    )
    assert len(findings) == 1
    assert findings[0].finding_status == FindingStatus.CONFIRMED_BY_SOURCE
    assert "hepatotoxicity" in findings[0].evidence_text.lower()
