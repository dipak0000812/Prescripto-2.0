import io, json, os, re, sys
import ollama
from PIL import Image
from rapidfuzz import fuzz

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
DATA_DIR = r"C:\Users\Admin\Desktop\prescripto data"
LABELS = os.path.join(ROOT, r"data\labels\drug_labels.json")
WHOLE = os.path.join(ROOT, r"outputs\vlm")
OUT = os.path.join(ROOT, r"outputs\vlm_strips")
MODEL = "qwen2.5vl:7b"
N_STRIPS, OVERLAP = 3, 0.12
PREFIX = r"^(tab|tas|cap|syp|inj|t|pb)\b[\.\s]*"
os.makedirs(OUT, exist_ok=True)

PROMPT = ("This is a photo of part of a medical prescription. List every medicine name written on it, "
          "exactly as written, including any strength number printed next to it. "
          "Do not correct spelling. Do not add medicines that are not on the page. "
          "Skip anything you cannot read. "
          'Return JSON only: {"medicines": ["name 1", "name 2"]}')


def norm(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(PREFIX, "", s.strip(), flags=re.I).lower())


files = {}
for f in sorted(os.listdir(DATA_DIR)):
    if f.lower().endswith((".jpg", ".jpeg", ".png")):
        files.setdefault(os.path.splitext(f)[0], f)

run_all = sys.argv[1:] == ["all"]
if run_all:
    ids = sorted(files, key=lambda s: int(s) if s.isdigit() else 0)
else:
    with open(LABELS, encoding="utf-8-sig") as fh:
        ids = [str(r["image"]) for r in json.load(fh)]

for pid in ids:
    dest = os.path.join(OUT, f"{pid}.json")
    if run_all and os.path.exists(dest):
        continue
    try:
        img = Image.open(os.path.join(DATA_DIR, files[pid])).convert("RGB")
        W, H = img.size
        names = []
        wp = os.path.join(WHOLE, f"{pid}.json")
        if os.path.exists(wp):
            with open(wp, encoding="utf-8") as fh:
                names += [m["medication_name"]["values"][0] for m in json.load(fh)["medications"]]
        step = H / N_STRIPS
        boxes = [(0, max(0, int(i * step - OVERLAP * H)), W, min(H, int((i + 1) * step + OVERLAP * H)))
                 for i in range(N_STRIPS)] if H >= 300 else []
        for b in boxes:
            buf = io.BytesIO()
            img.crop(b).save(buf, format="JPEG", quality=95)
            resp = ollama.chat(model=MODEL, format="json", options={"temperature": 0},
                               messages=[{"role": "user", "content": PROMPT, "images": [buf.getvalue()]}])
            try:
                names += [str(n) for n in json.loads(resp["message"]["content"]).get("medicines", [])]
            except Exception:
                pass
        kept = []
        for n in names:
            n = n.strip()
            nn = norm(n)
            if len(nn) < 3 or any(fuzz.ratio(nn, k) >= 90 for _, k in kept):
                continue
            kept.append((n, nn))
        data = {"image": pid, "medications": [{"medication_name": {"values": [n]}} for n, _ in kept]}
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print(f"{pid}: {len(kept)} names")
    except Exception as e:
        print(f"{pid}: ERROR {e}")