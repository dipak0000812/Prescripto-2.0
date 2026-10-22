"""
Unit tests for Enhanced Clinical Safety Screening & LLM Explainer.
Tests:
- Allergy contraindication detection
- High dosage safety limit warnings
- LLM Explainer deterministic synthesis
"""
import uuid
import pytest
from prescripto.domain.safety.models import (
    SafetyCheckType,
    FindingStatus,
)
from prescripto.domain.medication.models import CanonicalMedication
from prescripto.domain.safety.allergy import detect_allergy_contraindications
from prescripto.domain.safety.dosage import detect_dosage_safety_warnings
from prescripto.application.services.llm_explainer import LLMExplainerService


def test_detect_allergy_contraindication_penicillin_cross_reactivity():
    analysis_id = uuid.uuid4()
    med1_id = uuid.uuid4()
    
    # Amoxicillin is a penicillin-class antibiotic
    canonical_amox = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Moxclav 625",
        generic_name="Amoxicillin and Potassium Clavulanate",
        active_ingredients=["Amoxicillin", "Clavulanic Acid"],
        strength="625mg",
    )
    
    medication_lines = [
        (med1_id, "Moxclav 625", canonical_amox),
    ]
    
    # Patient has known penicillin allergy
    patient_allergies = "Penicillin, Sulfa drugs"
    findings = detect_allergy_contraindications(analysis_id, patient_allergies, medication_lines)
    
    assert len(findings) >= 1
    f = findings[0]
    assert f.check_type == SafetyCheckType.ADVERSE_EFFECT
    assert f.finding_status == FindingStatus.CONFIRMED_BY_SOURCE
    assert f.medication_ids == [med1_id]
    assert "CRITICAL ALLERGY CONTRAINDICATION" in f.evidence_text
    assert "penicillin" in f.evidence_text.lower()


def test_detect_allergy_no_allergy_safe():
    analysis_id = uuid.uuid4()
    med1_id = uuid.uuid4()
    canonical_pcm = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Dolo 650",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        strength="650mg",
    )
    medication_lines = [
        (med1_id, "Dolo 650", canonical_pcm),
    ]
    
    # Patient has Sulfa allergy; Paracetamol should not flag
    findings = detect_allergy_contraindications(analysis_id, "Sulfa", medication_lines)
    assert len(findings) == 0


def test_detect_dosage_safety_warning_exceeds_threshold():
    analysis_id = uuid.uuid4()
    med1_id = uuid.uuid4()
    canonical = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol 1500mg",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        strength="1500mg",
    )
    
    med_lines = [
        (med1_id, "Calpol", "1500mg", "1500mg", canonical),
    ]
    
    findings = detect_dosage_safety_warnings(analysis_id, med_lines)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_type == SafetyCheckType.ADVERSE_EFFECT
    assert f.finding_status == FindingStatus.REQUIRES_REVIEW
    assert "DOSAGE SAFETY WARNING" in f.evidence_text
    assert "1500.0mg" in f.evidence_text


def test_llm_explainer_deterministic_fallback():
    service = LLMExplainerService(gemini_key=None, openai_key=None)
    
    medications = [
        {"name_raw": "Augmentin 625", "strength_raw": "625mg", "frequency_raw": "BD", "duration_raw": "5 days"},
        {"name_raw": "Dolo 650", "strength_raw": "650mg", "frequency_raw": "TDS", "duration_raw": "3 days"},
    ]
    findings = [
        {"evidence_text": "CRITICAL ALLERGY ALERT: Patient is allergic to Penicillin. Augmentin is contraindicated."}
    ]
    patient = {
        "name": "Rahul Verma",
        "age": 42,
        "allergies": "Penicillin",
    }
    
    result = service.explain(medications, findings, patient)
    assert result["llm_ready"] is True
    assert "Rahul Verma" in result["executive_summary"]
    assert len(result["patient_instructions"]) == 2
    assert "CRITICAL ALLERGY ALERT" in result["clinical_alerts"][0]
    assert len(result["doctor_recommendations"]) > 0
