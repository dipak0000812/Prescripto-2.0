import csv, json, os, re
from rapidfuzz import process, fuzz

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
VOCAB = os.path.join(ROOT, r"data\vocab\medicine_vocab.csv")
OCR_DIR = os.path.join(ROOT, r"outputs\ocr_paddle")
STR_DIR = os.path.join(ROOT, r"outputs\structured")
OUT_DIR = os.path.join(ROOT, r"outputs\normalized")
os.makedirs(OUT_DIR, exist_ok=True)

with open(VOCAB, encoding="utf-8") as fh:
    NAMES = [r["name"] for r in csv.DictReader(fh)]
LOWER = [n.lower() for n in NAMES]

def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)

def clean(s):
    s = re.sub(r"^[^A-Za-z0-9]+", "", s)
    s = re.sub(r"^(tab|tas|cap|syp|inj)\b\.?\s*", "", s, flags=re.I)
    return re.sub(r"[^A-Za-z0-9 ]", " ", s).strip().lower()

def cands(text, limit=3, cutoff=75):
    q = clean(text)
    if len(q) < 4:
        return []
    res = process.extract(q, LOWER, scorer=fuzz.WRatio, limit=limit, score_cutoff=cutoff)
    return [{"name": NAMES[i], "score": round(sc, 1)} for _, sc, i in res]

total = hit = 0
files = sorted((f for f in os.listdir(STR_DIR) if f.endswith(".json")),
               key=lambda s: int(s[:-5]) if s[:-5].isdigit() else 0)
for f in files:
    pid = f[:-5]
    data, items = load(os.path.join(STR_DIR, f)), load(os.path.join(OCR_DIR, f))
    covered = set()
    for m in data["medications"]:
        covered.update(m["line_ids"])
        name = (m["medication_name"]["values"] or [None])[0]
        m["vocab_candidates"] = cands(name) if name else []
        total += 1
        hit += bool(m["vocab_candidates"] and m["vocab_candidates"][0]["score"] >= 90)
    missed = []
    for i, d in enumerate(items):
        lid = f"L{i}"
        if lid in covered or d["score"] < 0.7:
            continue
        c = cands(d["text"], limit=1, cutoff=88)
        if c:
            missed.append({"line_id": lid, "text": d["text"], "score": d["score"], "closest": c[0]})
    data["possible_missed_drug_lines"] = missed
    data["normalization_note"] = "Fuzzy candidates only. Never auto-resolved; a reviewer decides."
    with open(os.path.join(OUT_DIR, f), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"{pid}: {len(data['medications'])} meds | {len(missed)} possible missed lines")
print(f"\nmedication names with a vocab candidate >=90: {hit}/{total}")