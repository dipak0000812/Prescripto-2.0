import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ocr.ppocr_adapter import PPOCRAdapter
from extraction.entity_extractor import clean_ocr_text, extract_entities

DATASET_FOLDER = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset"
TEST_IMAGES = ["1.jpg", "10.jpg", "45.jpg", "90.jpg", "100.jpg"]  # start with 5

adapter = PPOCRAdapter(device="gpu:0")

for fname in TEST_IMAGES:
    path = os.path.join(DATASET_FOLDER, fname)
    regions = adapter.detect_regions(path)
    full_text = " ".join(adapter.recognize_line(r)[0] for r in regions)
    cleaned = clean_ocr_text(full_text)
    entities = extract_entities(cleaned)

    print(f"\n--- {fname} ---")
    print("OCR TEXT:", cleaned)
    print("EXTRACTED:", entities)
    from normalization.medicine_matcher import fuzzy_match_medicine
    KNOWN_MEDICINES = ["Metformin", "Paracetamol", "Amoxicillin", "Digoxin", "Metoclopramide"]
    med, score = fuzzy_match_medicine(cleaned, KNOWN_MEDICINES)
    print("MEDICINE MATCH:", med, score)