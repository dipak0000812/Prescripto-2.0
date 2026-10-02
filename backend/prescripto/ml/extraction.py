"""Conservative rule-based field extraction from OCR transcription lines."""
from __future__ import annotations

import re
from typing import Any

from prescripto.domain.uncertainty.models import FieldState


PATTERNS: dict[str, re.Pattern[str]] = {
    "strength": re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|%)\b", re.IGNORECASE),
    "dose": re.compile(
        r"\b\d+(?:\.\d+)?\s?(?:tablets?|tabs?|capsules?|caps?|drops?|ml|puffs?)\b",
        re.IGNORECASE,
    ),
    "frequency": re.compile(
        r"\b(?:OD|BD|BID|TDS|TID|QID|QDS|once daily|twice daily|three times daily|four times daily|at night)\b",
        re.IGNORECASE,
    ),
    "route": re.compile(r"\b(?:oral|PO|topical|top|IM|IV|inhaled|ophthalmic)\b", re.IGNORECASE),
    "duration": re.compile(r"\b(?:for\s+)?\d+\s?(?:days?|weeks?)\b", re.IGNORECASE),
    "instructions": re.compile(
        r"\b(?:after food|after meals|before food|before meals|before breakfast|with food|empty stomach|at bedtime|SOS|PRN)\b",
        re.IGNORECASE,
    ),
}


def _field(value: str | None, unreadable: bool = False) -> dict[str, Any]:
    if value is None:
        return {
            "raw": None,
            "state": FieldState.UNREADABLE.value if unreadable else FieldState.NOT_PRESENT.value,
            "confidence": None,
        }
    return {
        "raw": value.strip(),
        "state": FieldState.AMBIGUOUS.value,
        "confidence": None,
    }


def extract_prescription_fields(text: str) -> dict[str, dict[str, Any]]:
    """Extract explicit spans only; all OCR-derived values remain review-required."""
    line = " ".join(text.split())
    matches = {name: pattern.search(line) for name, pattern in PATTERNS.items()}
    value_by_name = {
        name: match.group(0) if match else None for name, match in matches.items()
    }

    if not line:
        return {
            "name": _field(None, unreadable=True),
            **{name: _field(None) for name in PATTERNS},
            "unit": _field(None),
        }

    field_spans = [match.start() for match in matches.values() if match]
    name_end = min(field_spans) if field_spans else len(line)
    name_value = line[:name_end].strip(" ,;:-") or None

    dose_value = value_by_name["dose"]
    unit_value = None
    if dose_value:
        unit_match = re.search(
            r"(?:tablets?|tabs?|capsules?|caps?|drops?|ml|puffs?)$",
            dose_value,
            re.IGNORECASE,
        )
        unit_value = unit_match.group(0) if unit_match else None

    output = {name: _field(value) for name, value in value_by_name.items()}
    output["name"] = _field(name_value)
    output["unit"] = _field(unit_value)
    return output
