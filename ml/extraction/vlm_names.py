import io, json, os, sys
import ollama
from PIL import Image

ROOT = os.environ.get("PRESCRIPTO_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.environ.get("PRESCRIPTO_DATA_DIR") or os.path.join(ROOT, "data", "prescriptions")
LABELS = os.path.join(ROOT, "data", "labels", "drug_labels.json")
OUT = os.path.join(ROOT, "outputs", "vlm")
MODEL = os.environ.get("VLM_MODEL", "qwen2.5vl:7b")
EXTS = (".jpg", ".jpeg", ".png")
os.makedirs(OUT, exist_ok=True)

PROMPT = ("This is a photo of a medical prescription. List every medicine name written on it, "
          "exactly as written, including any strength number printed next to it. "
          "Do not correct spelling. Do not add medicines that are not on the page. "
          "Skip anything you cannot read. "
          'Return JSON only: {"medicines": ["name 1", "name 2"]}')

files = {}
for f in sorted(os.listdir(DATA_DIR)):
    if f.lower().endswith(EXTS):
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
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        resp = ollama.chat(model=MODEL, format="json", options={"temperature": 0},
                           messages=[{"role": "user", "content": PROMPT, "images": [buf.getvalue()]}])
        try:
            names = json.loads(resp["message"]["content"]).get("medicines", [])
        except Exception:
            names = []
        names = list(dict.fromkeys(str(n).strip() for n in names if str(n).strip()))
        data = {"image": pid, "medications": [{"medication_name": {"values": [n]}} for n in names]}
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print(f"{pid}: {len(names)} names")
    except Exception as e:
        print(f"{pid}: ERROR {e}")