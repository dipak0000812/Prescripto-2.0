from jiwer import wer
from rapidfuzz.distance import Levenshtein

ground_truth = (
    "Dr B. Who Farmstreet 12 Kirkville tel. 3876 R/ "
    "date 1 Nov 1994 Digoxin 0.125 mg tablet da no.7 "
    "S 1 dd 1 tablet"
)

ocr_text = (
    "Dr B. Who Farmstreet 12 Kirkville tel. 3876 R/ "
    "date 1 wor 1994 Dijoxin 0.125 ing tatlch da no.7 "
    "5 1 dd 1 tarlet B. WAO Ms/Mr Pahient 30 address: wosh at ose"
)

cer = Levenshtein.normalized_distance(ground_truth, ocr_text)
word_error_rate = wer(ground_truth, ocr_text)

print(f"CER: {cer * 100:.2f}%")
print(f"WER: {word_error_rate * 100:.2f}%")