import csv
from pathlib import Path

from paddleocr import PaddleOCR
from jiwer import wer
from rapidfuzz.distance import Levenshtein


DATA_DIR = Path(r"C:\Users\Admin\Desktop\prescription_project\data")
CSV_PATH = DATA_DIR / "paddleocr_dataset_ground_truth.csv"

ocr = PaddleOCR(device="gpu:0")

total_cer = 0
total_wer = 0
count = 0

with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        image_path = DATA_DIR / "paddleocr_dataset" / row["image_path"]
        ground_truth = row["ground_truth_text"]

        # Skip image 1 for now because the original 1.jpg is actually GIF data.
        if row["image_id"] == "1":
            continue

        results = ocr.predict(str(image_path))

        ocr_text = " ".join(
            results[0]["rec_texts"]
        )

        cer = Levenshtein.normalized_distance(
            ground_truth, ocr_text
        )

        word_error_rate = wer(
            ground_truth, ocr_text
        )

        total_cer += cer
        total_wer += word_error_rate
        count += 1

        print(f"{row['image_id']}: CER={cer*100:.2f}%  WER={word_error_rate*100:.2f}%")

print("\n===== DATASET BASELINE =====")
print(f"Images evaluated: {count}")
print(f"Average CER: {(total_cer/count)*100:.2f}%")
print(f"Average WER: {(total_wer/count)*100:.2f}%")