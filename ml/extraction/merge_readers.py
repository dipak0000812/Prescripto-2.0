import csv, json, os, re, sys
from rapidfuzz import fuzz, process

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
OCR = os.path.join(ROOT, r"outputs\ocr_paddle")
VLM = os.path.join(ROOT, r"outputs\vlm")
STR = os.path.join(ROOT, r"outputs\structured")
OUT = os.path.join(ROOT, r"outputs\final")
VOCAB = os.path.join(ROOT, r"data\vocab\medicine_vocab.csv")
T = 80
FIELDS = ("strength", "dose", "frequency", "duration", "route", "instructions")
os.makedirs(OUT, exist_ok=True)
PREFIX = r"^(tab|tas|cap|syp|inj|t|pb)\b[\.\s]*"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(PREFIX, "", s.strip(), flags=re.I).lower())


def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


names = []
if os.path.exists(VOCAB):
    with open(VOCAB, encoding="utf-8") as fh:
        names = [r["name"] for r in csv.DictReader(fh)]
lower = [n.lower() for n in names]


def candidates(name):
    q = re.sub(r"[^a-z0-9 ]", " ", re.sub(PREFIX, "", name.strip(), flags=re.I).lower()).strip()
    if not names or len(q) < 4:
        return []
    res = process.extract(q, lower, scorer=fuzz.WRatio, limit=3, score_cutoff=75)
    return [{"name": names[i], "score": round(s, 1)} for _, s, i in res]


def name_entry(raw, agreement):
    return {"raw_text": raw, "state": "AMBIGUOUS", "reader_agreement": agreement,
            "review_priority": "standard" if agreement == "both_readers" else "high",
            "vocab_candidates": candidates(raw)}


def build(pid):
    paddle = norm(" ".join(d["text"] for d in load(os.path.join(OCR, f"{pid}.json"))))
    vp, qp = os.path.join(VLM, f"{pid}.json"), os.path.join(STR, f"{pid}.json")
    vlm = [m["medication_name"]["values"][0] for m in load(vp)["medications"]] if os.path.exists(vp) else []
    qwen = load(qp)["medications"] if os.path.exists(qp) else []
    used, meds = set(), []
    for n in vlm:
        nn = norm(n)
        if len(nn) < 3:
            continue
        agree = len(nn) >= 4 and fuzz.partial_ratio(nn, paddle) >= T
        entry = {"medication_name": name_entry(n, "both_readers" if agree else "vlm_only")}
        for i, q in enumerate(qwen):
            qn = norm((q["medication_name"]["values"] or [""])[0])
            if qn and len(qn) >= 4 and i not in used and fuzz.partial_ratio(nn, qn) >= 85:
                used.add(i)
                entry["details_from_paddle_text"] = {f: q[f]["values"] for f in FIELDS}
                break
        meds.append(entry)
    for i, q in enumerate(qwen):
        nm = (q["medication_name"]["values"] or [None])[0]
        if i in used or not nm or len(norm(nm)) < 4:
            continue
        meds.append({"medication_name": name_entry(nm, "paddle_only"),
                     "details_from_paddle_text": {f: q[f]["values"] for f in FIELDS}})
    return {"prescription_id": pid, "review_required": True, "medications": meds,
            "note": "Agreement flag is a pilot-measured review hint (n=13 images), not calibrated confidence."}


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["all"]:
        args = sorted((f[:-5] for f in os.listdir(OCR) if f.endswith(".json")),
                      key=lambda s: int(s) if s.isdigit() else 0)
    tot = {"both_readers": 0, "vlm_only": 0, "paddle_only": 0}
    for pid in args:
        res = build(pid)
        for m in res["medications"]:
            tot[m["medication_name"]["reader_agreement"]] += 1
        with open(os.path.join(OUT, f"{pid}.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
    print(f"{len(args)} images -> {OUT}")
    print(tot)