"""Conservative rule-based field extraction from OCR transcription lines."""
from __future__ import annotations

import re
from typing import Any

from prescripto.domain.uncertainty.models import FieldState

def clean_ocr_text(text: str) -> str:
    """Fix common OCR digit/letter confusions inside number+unit tokens, normalize abbreviations, and strip artifacts."""
    def fix_token(match: re.Match) -> str:
        token = match.group(0)
        return token.replace('O', '0').replace('o', '0').replace('Z', '2')

    # Convert volume misreads like '15 me' or '15 m1' to '15ml'
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s*(?:me|m1|mi)\b', r'\1ml', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[\dOoZ]+(?:mg|mcg|g|ml|ing|ong)\b', fix_token, text, flags=re.IGNORECASE)
    
    # Normalize common OCR cursive abbreviation misreads: Tn -> Tr. (Tincture)
    text = re.sub(r'\bTn\b', 'Tr. ', text)
    text = re.sub(r'^Tn(?=[A-Z])', 'Tr. ', text)
    
    text = text.strip().rstrip(':')
    return text


FORM_BOILERPLATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bDD\s*FORM(?:\s*\d+)?\b", re.IGNORECASE),
    re.compile(r"\bDOD\s+PRESCRIPTION\b", re.IGNORECASE),
    re.compile(r"\bPATIENT\s+(?:IDENTIFICATION|INFO|DATA|ID)?\b", re.IGNORECASE),
    re.compile(r"\b(?:SSN|SOCIAL\s+SECURITY)\b(?:\s*[:#]?\s*[\d\-]+)?", re.IGNORECASE),
    re.compile(r"\bMFGR\b(?:\s*[:#]?\s*[\w\.\-]+)?", re.IGNORECASE),
    re.compile(r"\bDISPENSED\s+BY\b", re.IGNORECASE),
    re.compile(r"\bSIGNATURE\s+(?:OF\s+PRESCRIBER)?\b", re.IGNORECASE),
    re.compile(r"\b(?:RANK|GRADE|ORGANIZATION|DUTY\s+STATION)\b", re.IGNORECASE),
    re.compile(r"\bREFILLS?\s*:\s*\d+\b", re.IGNORECASE),
    re.compile(r"^\s*R[xX]\s*$", re.IGNORECASE),
    re.compile(r"\b(?:WARD|CLINIC|HOSPITAL)\s+NO\b", re.IGNORECASE),
    re.compile(r"\bREG(?:\.|\s+)?(?:NO|NUMBER)\b", re.IGNORECASE),
]


def is_form_boilerplate(text: str) -> bool:
    """Strict word-boundary detection of printed form metadata, headers, and footers."""
    stripped = text.strip()
    if not stripped or len(stripped) < 2:
        return True
    return any(p.search(stripped) is not None for p in FORM_BOILERPLATE_PATTERNS)


def extract_patient_name(lines: list[str]) -> str | None:
    """Extracts genuine patient name from prescription document text lines."""
    # 1. Look for explicit 'Patient Name: ...' or 'Name: ...'
    for line in lines:
        cleaned = line.strip()
        match = re.search(
            r"\b(?:Patient(?:\s+Name)?|Pt\.?\s*Name|Name)\s*[:#\-]?\s*([A-Za-z\.\s]{3,40})\b",
            cleaned,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip()
            # Clean common trailing metadata like 'Age/Gender: 34 / M'
            candidate = re.split(
                r"\b(?:Age|Gender|Sex|DOB|SSN|Rank|Date|Diag|Ph|Reg)\b",
                candidate,
                flags=re.IGNORECASE,
            )[0].strip(" ,;:-")
            # Ensure it's not a boilerplate label
            if candidate and len(candidate.split()) >= 2 and not is_form_boilerplate(candidate):
                return candidate

    # 2. Look for lines immediately following 'PATIENT IDENTIFICATION'
    found_patient_header = False
    for line in lines:
        cleaned = line.strip()
        if re.search(r"\bPATIENT\s+(?:IDENTIFICATION|INFO|DATA)\b", cleaned, re.IGNORECASE):
            found_patient_header = True
            post_header = re.sub(
                r".*?\bPATIENT\s+(?:IDENTIFICATION|INFO|DATA)\b[:\s\-]*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            ).strip()
            if post_header and len(post_header.split()) >= 2 and not is_form_boilerplate(post_header):
                return post_header
            continue
        if found_patient_header:
            if not is_form_boilerplate(cleaned) and len(cleaned.split()) in (2, 3, 4):
                if not re.search(r"\b(?:SSN|MILITARY|FORM|DATE|RANK|GRADE|RX)\b", cleaned, re.IGNORECASE):
                    return cleaned

    # 3. Fallback scan for standalone 2-3 word capitalized person name in the top 8 lines (e.g. 'John R. Doe')
    for line in lines[:8]:
        cleaned = line.strip()
        if is_form_boilerplate(cleaned):
            continue
        if re.search(r"\b(?:Dr\.|MBBS|MD|Clinic|Hospital|Center|Phone|Ph:|Reg|Date|Diagnosis|Rx)\b", cleaned, re.IGNORECASE):
            continue
        # Pattern: e.g. 'John R. Doe' or 'Rahul Verma'
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$", cleaned):
            return cleaned

    return None


PATTERNS: dict[str, re.Pattern[str]] = {
    "strength": re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|%|ing|ong)\b", re.IGNORECASE),
    "dose": re.compile(
        r"\b\d+(?:\.\d+)?\s?(?:tablets?|tabs?|capsules?|caps?|drops?|ml|puffs?|barlet|ta6|tupp|supp)\b",
        re.IGNORECASE,
    ),
    "frequency": re.compile(
        r"\b(?:OD|BD|BID|TDS|TID|QID|QDS|once daily|twice daily|three times daily|four times daily|at night|s\s?\d+\s?dd\s?\d+)\b",
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
    cleaned = clean_ocr_text(text)
    line = " ".join(cleaned.split())
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
    raw_name = line[:name_end].strip(" ,;:-") or None
    if raw_name:
        # Strip leading numbers/bullets/prefixes like "1. ", "2) ", "Rx: ", "• "
        name_value = re.sub(
            r"^(?:\d+\s*[\.\)\-:]+|\*|#\d+|[•\-\+]|Rx:?)\s*",
            "",
            raw_name,
            flags=re.IGNORECASE,
        ).strip(" ,;:-") or raw_name
    else:
        name_value = None

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
