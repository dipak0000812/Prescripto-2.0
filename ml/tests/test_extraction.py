"""
ML Service — Extraction Unit Tests.

No FastAPI, no PaddleOCR required.
Tests extract_prescription_fields() with hand-crafted inputs.
"""
from __future__ import annotations

import pytest
from ml.app.extraction.spans import extract_prescription_fields
from ml.app.schemas.perception import FieldState


def test_full_prescription_line_extracts_all_fields():
    text = "Augmentin 625mg 1 tab BD after food for 5 days"
    fields = extract_prescription_fields(text)
    assert fields["strength"]["raw"] == "625mg"
    assert fields["dose"]["raw"] is not None
    assert fields["frequency"]["raw"] is not None
    assert fields["instructions"]["raw"] is not None
    assert fields["duration"]["raw"] is not None


def test_empty_string_returns_unreadable_name():
    fields = extract_prescription_fields("")
    assert fields["name"]["state"] == FieldState.UNREADABLE.value


def test_absent_field_returns_not_present():
    text = "Paracetamol 500mg"
    fields = extract_prescription_fields(text)
    assert fields["duration"]["state"] == FieldState.NOT_PRESENT.value


def test_present_field_returns_ambiguous_state():
    text = "Metformin 500mg 1 tab OD"
    fields = extract_prescription_fields(text)
    assert fields["strength"]["state"] == FieldState.AMBIGUOUS.value


def test_unit_extracted_from_dose():
    text = "Digoxin 0.125mg 1 tablet"
    fields = extract_prescription_fields(text)
    assert fields["unit"]["raw"] is not None
    assert "tablet" in fields["unit"]["raw"].lower()


def test_name_is_text_before_first_field_match():
    text = "Amoxicillin 250mg capsule"
    fields = extract_prescription_fields(text)
    assert fields["name"]["raw"] is not None
    assert "Amoxicillin" in fields["name"]["raw"]
