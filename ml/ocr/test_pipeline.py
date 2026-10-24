import sys, os
ml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_dir = os.path.abspath(os.path.join(ml_dir, ".."))
for d in (repo_dir, ml_dir):
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from ml.ocr.ppocr_adapter import PPOCRAdapter
    from ml.extraction.entity_extractor import clean_ocr_text, extract_entities
    from ml.normalization.medicine_matcher import fuzzy_match_medicine
except ImportError:
    from ocr.ppocr_adapter import PPOCRAdapter
    from extraction.entity_extractor import clean_ocr_text, extract_entities
    from normalization.medicine_matcher import fuzzy_match_medicine

DEFAULT_IMAGE = os.path.join(os.path.dirname(__file__), "..", "..", "sample_prescription.png")
IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("TEST_IMAGE") or DEFAULT_IMAGE)

KNOWN_MEDICINES = ["Metformin", "Paracetamol", "Amoxicillin", "Ibuprofen", "Atorvastatin", "Digoxin"]

def main():
    device = os.environ.get("OCR_DEVICE", "cpu")
    adapter = PPOCRAdapter(device=device)
    regions = adapter.detect_regions(IMAGE_PATH)

    full_text = ""
    for region_id in regions:
        text, score = adapter.recognize_line(region_id)
        print(f"{score:.3f}  {text}")
        full_text += text + " "

    cleaned = clean_ocr_text(full_text)
    entities = extract_entities(cleaned)
    print("\nEXTRACTED:", entities)

    med, score = fuzzy_match_medicine(cleaned, KNOWN_MEDICINES)
    print(f"FUZZY MEDICINE MATCH: {med} (score={score})")

if __name__ == "__main__":
    main()