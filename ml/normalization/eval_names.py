import csv, json, os, re, sys
from rapidfuzz import fuzz


ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
LABELS = os.path.join(ROOT, r"data\labels\drug_labels.csv")
STR_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, r"outputs\structured")
OCR_DIR = os.path.join(ROOT, r"outputs\ocr_paddle")


def norm(s):
    s = re.sub(r"^(tab|tas|cap|syp|inj)\b\.?\s*", "", s.strip(), flags=re.I)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)

labels = {}
with open(LABELS, encoding="utf-8-sig") as fh:
    text = fh.read()
try:
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("labels") or data.get("data") or [data]
except Exception:
    data = []
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        try:
            data.append(json.loads(line))
        except Exception:
            pass
for rec in data:
    if not isinstance(rec, dict):
        continue
    img = re.sub(r"\.\w+$", "", str(rec.get("image", "")).strip())
    drugs = rec.get("drugs", rec.get("drug", []))
    if isinstance(drugs, str):
        drugs = [drugs]
    for d in drugs:
        if str(d).strip():
            labels.setdefault(img, []).append(norm(d))
if not labels:
    print("Could not read labels. File starts with:\n", text[:400])
    raise SystemExit
print(f"Loaded {sum(len(v) for v in labels.values())} labeled drugs from {len(labels)} images: "
      f"{sorted(labels, key=lambda s: int(s) if s.isdigit() else 0)}")

def hit(a, b, t):
    return fuzz.ratio(a, b) >= t or (len(a) >= 5 and fuzz.partial_ratio(a, b) >= t)


for T in (80, 90):
    n_lab = ocr_ok = ext_ok = n_ext = ext_good = 0
    misses = []
    for img, drugs in labels.items():
        ocr = norm(" ".join(d["text"] for d in load(os.path.join(OCR_DIR, f"{img}.json"))))
        ext = [norm(v) for m in load(os.path.join(STR_DIR, f"{img}.json"))["medications"]
               for v in m["medication_name"]["values"]]
        n_ext += len(ext)
        ext_good += sum(any(hit(d, e, T) for d in drugs) for e in ext)
        for d in drugs:
            n_lab += 1
            in_ocr = len(d) >= 4 and fuzz.partial_ratio(d, ocr) >= T
            in_ext = any(hit(d, e, T) for e in ext)
            ocr_ok += in_ocr
            ext_ok += in_ext
            if not in_ext:
                misses.append((img, d, "OCR missed it" if not in_ocr else "OCR had it, extraction lost it"))
    print(f"\n=== match threshold {T} | {len(labels)} images | {n_lab} labeled drugs ===")
    print(f"OCR recall (drug present in Paddle text): {ocr_ok}/{n_lab} = {ocr_ok/n_lab:.0%}")
    print(f"Extraction recall (drug in Qwen output) : {ext_ok}/{n_lab} = {ext_ok/n_lab:.0%}")
    print(f"Extraction precision (names that are real drugs): {ext_good}/{n_ext} = {ext_good/max(n_ext,1):.0%}")
    if T == 80:
        for m in misses:
            print("MISS", m)