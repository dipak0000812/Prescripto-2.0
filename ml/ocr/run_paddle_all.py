import os, json
import numpy as np
from PIL import Image
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

ROOT = os.environ.get("PRESCRIPTO_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.environ.get("PRESCRIPTO_DATA_DIR") or os.path.join(ROOT, "data", "prescriptions")
OUT_DIR = os.path.join(ROOT, "outputs", "ocr_paddle")
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
MIN_SCORE = 0.5

os.makedirs(OUT_DIR, exist_ok=True)
if HAS_PADDLE:
    device = os.environ.get("PADDLE_DEVICE", "cpu")
    ocr = PaddleOCR(device=device)
else:
    ocr = None

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