"""
Slice 6 — Normalization
Fuzzy string matching to resolve OCR'd medicine names against a known list.
Per ML-ARCHITECTURE.md: normalization is fuzzy/phonetic matching, not a model.
"""

from rapidfuzz import fuzz, process


def fuzzy_match_medicine(text: str, known_medicines: list, threshold: int = 70):
    """
    Find the closest known medicine name inside a text string.
    Returns (matched_name, score) or (None, best_score) if below threshold.
    """
    words = (
        text.replace(",", " ")
        .replace(".", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("_", " ")
        .split()
    )

    best_match = None
    best_score = 0

    for word in words:
        if not word.strip():
            continue
        match, score, _ = process.extractOne(word, known_medicines, scorer=fuzz.ratio)
        if score > best_score:
            best_score = score
            best_match = match

    if best_score >= threshold:
        return best_match, best_score
    return None, best_score