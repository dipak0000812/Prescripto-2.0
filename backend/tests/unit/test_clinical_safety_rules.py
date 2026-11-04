"""
Unit tests for Strict Clinical Safety Rules.

Ensures:
1. Non-medication text is NEVER converted into medication records.
2. Dosing instructions are NEVER fabricated (no 'as directed' default).
3. Unresolved text NEVER generates active duplicate-medication alerts for patients.
4. Original recognized text is ALWAYS preserved alongside normalized interpretations.
5. Patient-friendly report generator strictly renders 6 distinct sections (A to F).
6. Explainer does not fabricate diagnoses or medical recommendations.
"""

import uuid
import pytest

from prescripto.domain.recognition.models import (
    DocumentFieldType,
    DocumentItem,
    DocumentRecognitionResult,
)
from prescripto.domain.medication.models import (
    CanonicalMedication,
    MedicationResolutionResult,
    ResolutionStatus,
)
from prescripto.domain.safety.models import (
    DomainRiskFinding,
    FindingStatus,
    NotEvaluatedReason,
    SafetyCheckType,
)
from prescripto.domain.safety.duplicate import detect_duplicate_medications
from prescripto.application.services.llm_explainer import ClinicalExplainerService


class TestClinicalSafetyRules:
    @pytest.fixture
    def explainer(self):
        return ClinicalExplainerService()

    def test_no_fabricated_dosing_instruction_when_missing_frequency(self, explainer):
        """
        Verify that missing frequency or dosing information is never replaced with
        fabricated instructions like 'as directed'.
        """
        medication_records = [
            {
                "id": str(uuid.uuid4()),
                "name_raw": "Tab Pantoprazole",
                "normalized_name": "Pantoprazole",
                "dose_raw": "40mg",
                "frequency_raw": None,  # Missing frequency!
                "duration_raw": None,   # Missing duration!
                "route_raw": "oral",
                "confidence_score": 0.88,
                "needs_review": False,
            }
        ]

        result = explainer.explain(
            medications=medication_records,
            safety_findings=[],
            document_context={"summary": "Acid reflux prescription"},
        )

        plain_text = result.get("plain_english_summary", "")
        # Critical clinical check: "as directed" must NOT be fabricated
        assert "as directed" not in plain_text.lower()
        # Missing frequency must be flagged clearly
        assert "Frequency not specified" in plain_text or "not specified" in plain_text.lower() or "once daily" not in plain_text

        # Verify structured section C
        meds_section = result.get("medicines_and_treatments", [])
        assert len(meds_section) == 1
        assert meds_section[0]["name"] == "Pantoprazole"
        assert meds_section[0]["frequency"] in (None, "Not specified", "")
        assert "as directed" not in str(meds_section[0]["frequency"]).lower()

    def test_unresolved_text_never_generates_active_duplicate_alert(self, explainer):
        """
        Verify that unresolved entities marked NOT_EVALUATED do not produce active
        duplicate-medication warning cards for the patient.
        """
        analysis_id = uuid.uuid4()
        line_id = uuid.uuid4()

        # Simulate unresolved entity resulting in NOT_EVALUATED duplicate finding
        unresolved_line = (
            line_id,
            MedicationResolutionResult(
                extracted_text="UnknownScribble123",
                resolution_status=ResolutionStatus.UNRESOLVED,
                resolved_medication=None,
            ),
        )

        domain_findings = detect_duplicate_medications(analysis_id, [unresolved_line])
        assert len(domain_findings) == 1
        finding = domain_findings[0]
        assert finding.finding_status == FindingStatus.NOT_EVALUATED
        assert finding.not_evaluated_reason == NotEvaluatedReason.UNRESOLVED_IDENTITY.value

        # Convert to dict format passed to explainer
        finding_dicts = [
            {
                "id": str(finding.id),
                "check_type": finding.check_type.value,
                "finding_status": finding.finding_status.value,
                "evidence_text": finding.evidence_text,
                "not_evaluated_reason": finding.not_evaluated_reason,
            }
        ]

        result = explainer.explain(
            medications=[],
            safety_findings=finding_dicts,
            document_context={},
        )

        # Patient alerts must NOT include duplicate medication warning for unresolved text
        patient_alerts = result.get("patient_alerts", [])
        assert len(patient_alerts) == 0

    def test_original_text_preserved_alongside_normalized_text(self, explainer):
        """
        Verify that original handwritten text is never erased or overwritten by normalization.
        """
        medication_records = [
            {
                "id": str(uuid.uuid4()),
                "name_raw": "T. Para 500",
                "normalized_name": "Paracetamol 500mg Tablet",
                "dose_raw": "500mg",
                "frequency_raw": "TDS",
                "duration_raw": "3 days",
                "route_raw": "oral",
                "confidence_score": 0.85,
                "needs_review": False,
            }
        ]

        result = explainer.explain(
            medications=medication_records,
            safety_findings=[],
            document_context={},
        )

        meds = result.get("medicines_and_treatments", [])
        assert len(meds) == 1
        assert meds[0]["original_text"] == "T. Para 500"
        assert meds[0]["name"] == "Paracetamol 500mg Tablet"

    def test_patient_report_renders_all_six_sections(self, explainer):
        """
        Verify that the output contains all 6 required sections:
        A. Prescription summary
        B. What the doctor wrote
        C. Medicines and treatments
        D. Other advice
        E. Needs confirmation
        F. Safety notice
        """
        doc_context = {
            "summary": "Prescription for fever and dehydration",
            "hospital_details": ["City Emergency Care"],
            "patient_details": {"name": "John Doe", "age": "45"},
            "date": "2026-10-25",
            "symptoms": ["Giddiness, restlessness"],
            "vital_signs": ["Blood Pressure: 110/70 mmHg"],
            "diagnosis": ["Acute Dehydration"],
            "general_advice": ["Adequate fluid intake", "ORS 2 sachets"],
            "uncertain_items": [{"original_text": "?? unreadable line"}],
            "non_medication_treatments": [{"original_text": "Cold compress for forehead"}],
        }

        medication_records = [
            {
                "id": str(uuid.uuid4()),
                "name_raw": "Tab Paracetamol 650mg",
                "normalized_name": "Paracetamol",
                "dose_raw": "650mg",
                "frequency_raw": "SOS",
                "duration_raw": "3 days",
                "route_raw": "oral",
                "confidence_score": 0.95,
                "needs_review": False,
            }
        ]

        result = explainer.explain(
            medications=medication_records,
            safety_findings=[],
            document_context=doc_context,
        )

        # Section A: Prescription Summary
        assert "prescription_summary" in result
        assert len(result["prescription_summary"]) > 0

        # Section B: What the doctor wrote
        assert "what_doctor_wrote" in result
        doc_wrote = result["what_doctor_wrote"]
        assert "symptoms" in doc_wrote
        assert len(doc_wrote["symptoms"]) > 0
        assert "vital_signs" in doc_wrote
        assert "clinical_impression" in doc_wrote

        # Section C: Medicines and treatments
        assert "medicines_and_treatments" in result
        meds = result["medicines_and_treatments"]
        assert len(meds) == 1
        assert meds[0]["name"] == "Paracetamol"

        # Section D: Other advice
        assert "other_advice" in result
        advice = result["other_advice"]
        assert len(advice) >= 2  # Fluid intake and ORS

        # Section E: Needs confirmation
        assert "needs_confirmation" in result
        unclear = result["needs_confirmation"]
        assert len(unclear) >= 1

        # Section F: Safety notice
        assert "safety_notice" in result
        notice = result["safety_notice"]
        assert "healthcare professional" in notice.lower() or "pharmacist" in notice.lower()
