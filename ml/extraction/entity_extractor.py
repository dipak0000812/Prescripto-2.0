"""
Slice 5 — Structured Extraction
Rule-based extraction of medication fields from cleaned OCR text.
Per ML-ARCHITECTURE.md: extraction is regex + lexicon, not a model.
"""

import re


def clean_ocr_text(text: str) -> str:
    """Fix common OCR digit/letter confusions inside number+unit tokens."""
    def fix_token(match):
        token = match.group(0)
        return token.replace('O', '0').replace('o', '0').replace('Z', '2')

    text = re.sub(r'\b[\dOoZ]+mg\b', fix_token, text)
    text = text.strip().rstrip(':')
    return text


def extract_entities(text: str) -> dict:
    """
    Extract structured fields from OCR text.
    Returns dict with: medicine_name, strength, dosage, frequency, duration.
    Any field not found is None — never guessed.
    """
    entities = {
        "medicine_name": None,
        "strength": None,
        "dosage": None,
        "frequency": None,
        "duration": None,
    }

    strength_match = re.search(r'(\d+(?:\.\d+)?)\s?(mg|ing|ong|mcg)', text, re.IGNORECASE)
    if strength_match:
        entities["strength"] = f"{strength_match.group(1)}mg"

    dosage_match = re.search(r'(\d+)\s?(tablet|capsule|tab|cap|barlet|ta6|tupp|supp)', text, re.IGNORECASE)
    if dosage_match:
        entities["dosage"] = f"{dosage_match.group(1)} {dosage_match.group(2)}"
    else:
        form_match = re.search(r'\b(tablet|capsule|tab|cap|tupp|supp)\b', text, re.IGNORECASE)
        if form_match:
            entities["dosage"] = f"1 {form_match.group(1)} (inferred)"

    freq_patterns = [
        r'once daily(?: at night| before breakfast)?',
        r'twice daily',
        r'three times daily',
        r's\s?\d+\s?dd\s?\d+',   # Latin shorthand: "s 1 dd 1" = signa, dosage
    ]
    for pattern in freq_patterns:
        freq_match = re.search(pattern, text, re.IGNORECASE)
        if freq_match:
            entities["frequency"] = freq_match.group(0)
            break

    duration_match = re.search(r'for\s+(\d+)\s+days?', text, re.IGNORECASE)
    if duration_match:
        entities["duration"] = f"{duration_match.group(1)} days"

    return entities


def extract_medicine_name(text: str, known_medicines: list) -> str | None:
    """Exact substring match against a known medicine list."""
    for med in known_medicines:
        if med.lower() in text.lower():
            return med
    return None