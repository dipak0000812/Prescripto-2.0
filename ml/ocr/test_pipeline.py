import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ocr.ppocr_adapter import PPOCRAdapter
from extraction.entity_extractor import clean_ocr_text, extract_entities
from normalization.medicine_matcher import fuzzy_match_medicine

KNOWN_MEDICINES = ["Metformin", "Paracetamol", "Amoxicillin", "Ibuprofen", "Atorvastatin", "Digoxin"]
IMAGE_PATH = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset\1_test.jpg"

def main():
    adapter = PPOCRAdapter(device="gpu:0")
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