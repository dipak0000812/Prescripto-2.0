import os, json
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

DATA_DIR = r"C:\Users\Admin\Desktop\prescripto data"
OUT_DIR = r"C:\Users\Admin\Desktop\Prescripto-2.0\outputs\ocr_paddle"
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
MIN_SCORE = 0.5

os.makedirs(OUT_DIR, exist_ok=True)
ocr = PaddleOCR(device="gpu:0")

seen = {}
for f in sorted(os.listdir(DATA_DIR)):
    if f.lower().endswith(EXTS):
        seen.setdefault(os.path.splitext(f)[0], f)
files = [seen[k] for k in sorted(seen, key=lambda s: int(s) if s.isdigit() else 0)]
print(f"{len(files)} unique images")

for fname in files:
    try:
        arr = np.array(Image.open(os.path.join(DATA_DIR, fname)).convert("RGB"))
        r = ocr.predict(arr)[0]
        items = []
        for box, t, s in zip(r["rec_boxes"], r["rec_texts"], r["rec_scores"]):
            if t.strip() and float(s) >= MIN_SCORE:
                x1, y1, x2, y2 = [int(v) for v in box]
                items.append({"text": t, "score": round(float(s), 3), "box": [x1, y1, x2, y2]})
        items.sort(key=lambda d: ((d["box"][1] + d["box"][3]) // 2 // 25, d["box"][0]))
        with open(os.path.join(OUT_DIR, os.path.splitext(fname)[0] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
        print(f"{fname}: {len(items)} lines kept")
    except Exception as e:
        print(f"{fname}: ERROR {e}")