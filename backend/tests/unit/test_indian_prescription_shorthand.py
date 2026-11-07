"""
Table-driven unit tests for Indian prescription shorthand, form detection, and frequency parsing.
"""
import pytest
from prescripto.ml.extraction import extract_prescription_fields, clean_ocr_text


# 40+ real-world Indian prescription shorthand cases
SHORTHAND_CASES = [
    ("Tab Paracetamol 650mg 1-0-1 x 5 days", "Paracetamol", "650mg", "1-0-1", "5 days", "tablet"),
    ("CALPOL 250/5 syp 5ml TDS x 3 days", "CALPOL", "250/5", "TDS", "3 days", "syrup"),
    ("Calpol 120/5 susp 5ml q6h", "Calpol", "120/5", "q6h", None, "syrup"),
    ("Augmentin 625 BD pc x 7 days", "Augmentin", "625", "BD", "7 days", "tablet"),
    ("Azithral 500 OD x 3 days", "Azithral", "500", "OD", "3 days", "tablet"),
    ("Pan 40 OD ac 30 mins", "Pan", "40", "OD", None, "tablet"),
    ("Syp Ambrolite 1 tsp TID", "Ambrolite", None, "TID", None, "syrup"),
    ("Cap Omez 20mg OD empty stomach", "Omez", "20mg", "OD", None, "capsule"),
    ("Dolo 650 SOS for fever", "Dolo", "650", "SOS", None, "tablet"),
    ("Combiflam PRN for pain", "Combiflam", None, "PRN", None, "tablet"),
    ("Syp Corex DX 5ml q8h", "Corex DX", "5ml", "q8h", None, "syrup"),
    ("Inj Ceftriaxone 1g IV OD", "Ceftriaxone", "1g", "OD", None, "injection"),
    ("Candid cream apply BID", "Candid", None, "BID", None, "ointment"),
    ("Otrivin nasal drops 2 drops TDS", "Otrivin", None, "TDS", None, "drops"),
    ("Asthalin inhaler 2 puffs SOS", "Asthalin", None, "SOS", None, "inhaler"),
    ("Tab Pantocid 40 1-0-0 before food", "Pantocid", "40", "1-0-0", None, "tablet"),
    ("Tab Metformin 500mg 0-0-1 after food", "Metformin", "500mg", "0-0-1", None, "tablet"),
    ("Tab Telma 40 1-0-0", "Telma", "40", "1-0-0", None, "tablet"),
    ("Tab Ecosprin 75 0-1-0 after lunch", "Ecosprin", "75", "0-1-0", None, "tablet"),
    ("Amoxicillin 250mg/5ml susp 5ml TID", "Amoxicillin", "250mg/5ml", "TID", None, "syrup"),
    ("Cpm 4mg HS", "Cpm", "4mg", "HS", None, "tablet"),
    ("Tab Clonazepam 0.5mg at bedtime", "Clonazepam", "0.5mg", "at bedtime", None, "tablet"),
    ("Meftal Spas SOS for severe pain", "Meftal Spas", None, "SOS", None, "tablet"),
    ("Zincovit 1-0-0 x 1 month", "Zincovit", None, "1-0-0", "1 month", "tablet"),
    ("Becosules cap 1 daily x 15 days", "Becosules", None, "daily", "15 days", "capsule"),
    ("Tab Cifran 500 QID", "Cifran", "500", "QID", None, "tablet"),
    ("Volini gel local application BD", "Volini", None, "BD", None, "ointment"),
    ("Betadine oint apply twice daily", "Betadine", None, "twice daily", None, "ointment"),
    ("Ciplox eye drops 1 drop q4h", "Ciplox", None, "q4h", None, "drops"),
    ("Syp Zinc 20/5 5ml OD", "Zinc", "20/5", "OD", None, "syrup"),
    ("Unknownmed 50mg 1-0-1", "Unknownmed", "50mg", "1-0-1", None, None),
    ("Paracetamol 250/5", "Paracetamol", "250/5", None, None, "syrup"),
    ("Azithromycin 200/5 suspension", "Azithromycin", "200/5", None, None, "syrup"),
    ("Tab Voveran 50mg BD pc", "Voveran", "50mg", "BD", None, "tablet"),
    ("Tab Limcee 500mg chewable OD", "Limcee", "500mg", "OD", None, "tablet"),
    ("Duolin respules via nebulizer q6h", "Duolin", None, "q6h", None, "inhaler"),
    ("Tab Glycomet-GP 1 1-0-1 before meals", "Glycomet-GP 1", None, "1-0-1", None, "tablet"),
    ("Moxikind-CV 625 1 tab BID x 5 days", "Moxikind-CV", "625", "BID", "5 days", "tablet"),
    ("Supradyn 1 cap daily after breakfast", "Supradyn", None, "daily", None, "capsule"),
    ("Syrup Grilinctus 10ml thrice daily", "Grilinctus", "10ml", "thrice daily", None, "syrup"),
    ("Tab Rantac 150mg BD 30 min before food", "Rantac", "150mg", "BD", None, "tablet"),
    ("Tab Shelcal 500 0-0-1 with milk", "Shelcal", "500", "0-0-1", None, "tablet"),
    ("Crocin 120/5 syrup 5ml SOS", "Crocin", "120/5", "SOS", None, "syrup"),
    ("Mucaine gel 2 tsp after meals TDS", "Mucaine", None, "TDS", None, "syrup"),
]


@pytest.mark.parametrize("line,expected_name,expected_strength,expected_freq,expected_dur,expected_form", SHORTHAND_CASES)
def test_indian_prescription_shorthand_extraction(line, expected_name, expected_strength, expected_freq, expected_dur, expected_form):
    fields = extract_prescription_fields(line)

    if expected_strength:
        actual_strength = (fields.get("strength") or {}).get("raw")
        assert actual_strength is not None, f"Expected strength {expected_strength} in '{line}'"
        assert expected_strength.lower() in actual_strength.lower()

    if expected_freq:
        actual_freq = (fields.get("frequency") or {}).get("raw")
        assert actual_freq is not None, f"Expected frequency {expected_freq} in '{line}'"

    actual_form = (fields.get("form") or {}).get("raw")
    if expected_form is None:
        assert actual_form is None, f"Unknown drug '{line}' must not guess form, got '{actual_form}'"
    else:
        assert actual_form == expected_form, f"Expected form '{expected_form}' for '{line}', got '{actual_form}'"
