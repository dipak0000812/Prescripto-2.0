"""
Unit tests for Pure Domain Uncertainty & ExtractedField Propagation.
"""
import pytest
from prescripto.domain.uncertainty.models import (
    FieldState,
    ExtractedField,
    UncertaintyPropagationError,
)


def test_extracted_field_clear_propagation():
    field = ExtractedField(
        value="Amoxicillin 500mg",
        state=FieldState.CLEAR,
        confidence=0.98,
        raw_text="Amoxicillin 500mg",
    )
    propagated = field.propagate()
    assert propagated.state == FieldState.CLEAR
    assert propagated.value == "Amoxicillin 500mg"
    assert propagated.confidence == 0.98


def test_extracted_field_ambiguous_propagation():
    field = ExtractedField(
        value="Dolo 650?",
        state=FieldState.AMBIGUOUS,
        confidence=0.72,
        raw_text="Dolo 650?",
    )
    propagated = field.propagate()
    assert propagated.state == FieldState.AMBIGUOUS
    assert propagated.value == "Dolo 650?"


def test_extracted_field_unreadable_raises_propagation_error():
    field = ExtractedField(
        value=None,
        state=FieldState.UNREADABLE,
        confidence=0.15,
        raw_text="~~~scribble~~~",
    )
    with pytest.raises(UncertaintyPropagationError) as exc_info:
        field.propagate()
    assert "UNREADABLE field" in str(exc_info.value)


def test_extracted_field_not_present_propagation():
    field = ExtractedField(
        value=None,
        state=FieldState.NOT_PRESENT,
        confidence=0.0,
        raw_text="",
    )
    propagated = field.propagate()
    assert propagated.state == FieldState.NOT_PRESENT
    assert propagated.value is None


def test_extracted_field_confidence_out_of_bounds():
    with pytest.raises(ValueError):
        ExtractedField(
            value="Augmentin",
            state=FieldState.CLEAR,
            confidence=1.2,
            raw_text="Augmentin",
        )
