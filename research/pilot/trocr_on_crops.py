import json, os, re
import torch
from PIL import Image
from rapidfuzz import fuzz
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
DATA_DIR = r"C:\Users\Admin\Desktop\prescripto data"
OUT = os.path.join(ROOT, r"outputs\trocr_lines")
MODEL = "microsoft/trocr-base-handwritten"  # use microsoft/trocr-small-handwritten for a faster, smaller test
T, PAD = 80, 6
PREFIX = r"^(tab|tas|cap|syp|inj|t|pb)\b[\.\s]*"
os.makedirs(OUT, exist_ok=True)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(PREFIX, "", s.strip(), flags=re.I).lower())


def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


files = {}
for f in sorted(os.listdir(DATA_DIR)):
    if f.lower().endswith((".jpg", ".jpeg", ".png")):
        files.setdefault(os.path.splitext(f)[0], f)

labels = {str(r["image"]): [norm(d) for d in r["drugs"]]
          for r in load(os.path.join(ROOT, r"data\labels\drug_labels.json"))}

proc = TrOCRProcessor.from_pretrained(MODEL)
model = VisionEncoderDecoderModel.from_pretrained(MODEL).eval()


def recall(drugs, page):
    return sum(len(d) >= 4 and fuzz.partial_ratio(d, page) >= T for d in drugs)


tot = {"paddle": 0, "trocr": 0, "union": 0, "n": 0}
for img_id, drugs in labels.items():
    items = load(os.path.join(ROOT, rf"outputs\ocr_paddle\{img_id}.json"))
    img = Image.open(os.path.join(DATA_DIR, files[img_id])).convert("RGB")
    W, H = img.size
    lines = []
    for d in items:
        x1, y1, x2, y2 = d["box"]
        if x2 - x1 < 20 or y2 - y1 < 12:
            continue
        crop = img.crop((max(0, x1 - PAD), max(0, y1 - PAD), min(W, x2 + PAD), min(H, y2 + PAD)))
        pv = proc(images=crop, return_tensors="pt").pixel_values
        with torch.no_grad():
            ids = model.generate(pv, max_length=48, num_beams=3)
        lines.append({"box": d["box"], "paddle_text": d["text"],
                      "trocr_text": proc.batch_decode(ids, skip_special_tokens=True)[0]})
    with open(os.path.join(OUT, f"{img_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(lines, fh, ensure_ascii=False, indent=1)
    p = norm(" ".join(l["paddle_text"] for l in lines))
    t = norm(" ".join(l["trocr_text"] for l in lines))
    rp, rt, ru = recall(drugs, p), recall(drugs, t), recall(drugs, p + " " + t)
    tot["paddle"] += rp; tot["trocr"] += rt; tot["union"] += ru; tot["n"] += len(drugs)
    print(f"{img_id}: {len(lines)} crops | of {len(drugs)} drugs -> paddle {rp}, trocr {rt}, both {ru}")

n = tot["n"]
print(f"\nRecall over {n} labeled drugs (threshold {T}):")
for k in ("paddle", "trocr", "union"):
    print(f"  {k:7s}: {tot[k]}/{n} = {tot[k]/n:.0%}")