"""
Regression Tests for Previously Observed Handwriting OCR Failures.

Ensures that the application NEVER creates false medication entries or unsupported
dosing instructions (e.g. 'Take 22112122 - as directed') even when raw OCR produces
severely corrupted handwriting predictions.

Test cases:
1. "yuddbeu, yeublesny" (from "giddiness, restlessness")
2. "07011" (from "BP – 110/70")
3. "10% Dextrose (IV) stat."
4. "Adeauae Pluidtnbake" (from "Adequate fluid intake")
5. "RS2zache" (from "ORS 2 sachets")
6. "22112122" (from date "22/11/2022")
"""

import uuid
import pytest

from prescripto.domain.recognition.models import (
    DocumentFieldType,
    DocumentItem,
    DocumentRecognitionResult,
)
from prescripto.ml.recognition_providers import LocalRapidOCRProvider, classify_text_line
from prescripto.application.services.llm_explainer import ClinicalExplainerService


class TestPrescriptionFailuresRegression:
    @pytest.fixture
    def provider(self):
        return LocalRapidOCRProvider()

    @pytest.fixture
    def explainer(self):
        return ClinicalExplainerService()

    def test_symptoms_corruption_yuddbeu_yeublesny(self, provider, explainer):
        """
        'giddiness, restlessness' became 'yuddbeu, yeublesny'.
        The corrupted text must be preserved for human review, not guessed as symptoms or medicine.
        """
        raw_text = "yuddbeu, yeublesny"
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
        assert field_type != DocumentFieldType.MEDICATION_ORDER
        assert interpreted == raw_text

        # Verify explainer does not create medication card or dosing instruction
        doc_context = {"uncertain_items": [{"original_text": interpreted}]}
        report = explainer.explain(
            medications=[],
            findings=[],
            document_context=doc_context,
        )

        assert len(report["medicines_and_treatments"]) == 0
        plain_summary = report["plain_english_summary"]
        assert "Take yuddbeu" not in plain_summary
        assert report["needs_confirmation"]

    def test_vital_signs_corruption_07011(self, provider, explainer):
        """
        'BP – 110/70' became '07011'.
        The numeric OCR artifact must not be reconstructed into a blood pressure or medicine.
        """
        raw_text = "07011"
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
        assert field_type != DocumentFieldType.MEDICATION_ORDER
        assert interpreted == raw_text

        report = explainer.explain(
            medications=[],
            findings=[],
            document_context={"uncertain_items": [{"original_text": interpreted}]},
        )
        assert len(report["medicines_and_treatments"]) == 0
        assert "Take 07011" not in report["plain_english_summary"]

    def test_dextrose_iv_stat_preserves_exact_frequency(self, provider, explainer):
        """
        '10% Dextrose (IV) stat.'
        Regression invariant: If partially recognized, preserves 'stat' instruction,
        never invents daily frequency or 'as directed'.
        """
        raw_text = "10% Dextrose (IV) stat."
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.MEDICATION_ORDER

        med_record = {
            "id": str(uuid.uuid4()),
            "name_raw": "10% Dextrose",
            "normalized_name": "10% Dextrose IV Infusion",
            "dose_raw": "10%",
            "route_raw": "IV",
            "frequency_raw": "stat",
            "duration_raw": None,
        }

        report = explainer.explain(
            medications=[med_record],
            findings=[],
            document_context={},
        )

        meds = report["medicines_and_treatments"]
        assert len(meds) == 1
        assert meds[0]["frequency"] == "stat"
        assert "as directed" not in str(meds[0]["frequency"]).lower()

    def test_advice_corruption_adeauae_pluidtnbake(self, provider, explainer):
        """
        'Adequate fluid intake' became 'Adeauae Pluidtnbake'.
        The corrupted text must remain uncertain rather than being rewritten as advice.
        """
        raw_text = "Adeauae Pluidtnbake"
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
        assert field_type != DocumentFieldType.MEDICATION_ORDER
        assert interpreted == raw_text

        report = explainer.explain(
            medications=[],
            findings=[],
            document_context={"uncertain_items": [{"original_text": interpreted}]},
        )

        assert len(report["medicines_and_treatments"]) == 0
        assert report["other_advice"] == []
        assert report["needs_confirmation"]

    def test_treatment_corruption_rs2zache(self, provider, explainer):
        """
        'ORS 2 sachets' became 'RS2zache'.
        The corrupted text must remain uncertain, not be expanded into an ORS treatment.
        """
        raw_text = "RS2zache"
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
        assert field_type != DocumentFieldType.MEDICATION_ORDER
        assert interpreted == raw_text

        report = explainer.explain(
            medications=[],
            findings=[],
            document_context={"uncertain_items": [{"original_text": interpreted}]},
        )
        assert len(report["medicines_and_treatments"]) == 0

    def test_date_misclassification_22112122(self, provider, explainer):
        """
        The numeric OCR artifact must not be reconstructed into a date or medicine.
        """
        raw_text = "22112122"
        field_type, interpreted, reason = classify_text_line(raw_text)

        assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
        assert field_type != DocumentFieldType.MEDICATION_ORDER
        assert interpreted == raw_text

        report = explainer.explain(
            medications=[],
            findings=[],
            document_context={"uncertain_items": [{"original_text": interpreted}]},
        )
        assert len(report["medicines_and_treatments"]) == 0
        plain_summary = report["plain_english_summary"]
        assert "Take 22112122" not in plain_summary
        assert "Take 22112122 - as directed" not in plain_summary
        assert report["needs_confirmation"]

    def test_full_corrupted_prescription_prevents_false_medications(self, provider, explainer):
        """
        Full test with all previously observed errors occurring together in one prescription.
        Verifies that only genuine medication orders reach the medication table.
        """
        raw_lines = [
            "Apex Hospital Care",
            "22112122",
            "Pt Ramesh 52M",
            "yuddbeu, yeublesny",
            "07011",
            "Acute Dehydr",
            "10% Dextrose (IV) stat.",
            "Tab Paracetamol 650mg SOS",
            "RS2zache",
            "Adeauae Pluidtnbake",
        ]

        classified_items = [provider.classify_text_line(line) for line in raw_lines]

        # Filter strictly for MEDICATION_ORDER
        medication_items = [
            item for item in classified_items
            if item.field_type == DocumentFieldType.MEDICATION_ORDER
        ]

        # Only '10% Dextrose (IV) stat.' and 'Tab Paracetamol 650mg SOS' should be medication orders
        # All others (Hospital, Date, Patient, Symptoms, Vitals, Diagnosis, Advice, ORS) must NOT be medications
        med_texts = [m.original_text for m in medication_items]
        assert "22112122" not in med_texts
        assert "yuddbeu, yeublesny" not in med_texts
        assert "07011" not in med_texts
        assert "RS2zache" not in med_texts
        assert "Adeauae Pluidtnbake" not in med_texts

        assert any("Paracetamol" in t for t in med_texts)
