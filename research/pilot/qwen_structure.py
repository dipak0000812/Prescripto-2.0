import json, re, sys, os
import ollama
from rapidfuzz import fuzz

OUT_DIR = r"C:\Users\Admin\Desktop\Prescripto-2.0\outputs\ocr_paddle"
RES_DIR = r"C:\Users\Admin\Desktop\Prescripto-2.0\outputs\structured"
MODEL = "qwen2.5:7b-instruct"
FIELDS = ["medication_name", "strength", "dose", "frequency", "duration", "route", "instructions"]
FORMS = ["tab", "cap", "syp", "inj"]
os.makedirs(RES_DIR, exist_ok=True)

SYSTEM = """You convert OCR text of a prescription into structured medication entries.
STRICT RULES:
- Use ONLY text that appears in the OCR lines. Never add, complete, translate, or correct anything.
- Keep OCR spelling exactly (e.g. keep 'METO ER', keep '5O'). Never replace it with a drug name you know.
- If a field is not written, use null. Do not infer dose or frequency.
- Return one entry for EVERY line that starts with Tab/Cap/Syp/Inj or looks like a medicine name, even if other fields are null.
- Ignore headers, clinic info, dates, vitals, lab values, diagnoses, signatures.
- Cite the line ids (like "L3") each entry came from.
Return JSON only: {"medications":[{"line_ids":["L1"],"medication_name":str|null,"strength":str|null,"dose":str|null,"frequency":str|null,"duration":str|null,"route":str|null,"instructions":str|null}]}"""


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def is_candidate(text):
    toks = re.sub(r"^[^A-Za-z0-9]+", "", text).split()
    if not toks:
        return False
    t = toks[0].lower()[:3]
    return any(fuzz.ratio(t, p) >= 66 for p in FORMS)


def merge(entries):
    groups, order = {}, []
    for e in entries:
        nm = e["medication_name"]["value"]
        key = norm(nm) if nm else f"_unnamed_{len(order)}"
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)
    merged = []
    for key in order:
        g = groups[key]
        m = {
            "line_ids": sorted({i for e in g for i in e["line_ids"]}, key=lambda s: int(s[1:])),
            "source_texts": [e["source_text"] for e in g],
            "min_ocr_score": min(e["min_ocr_score"] for e in g),
            "occurrences": len(g),
        }
        for f in FIELDS:
            vals = []
            for e in g:
                v = e[f]["value"]
                if v is not None and v not in vals:
                    vals.append(v)
            states = [e[f]["state"] for e in g]
            if not vals:
                st = "AMBIGUOUS" if "AMBIGUOUS" in states else "NOT_PRESENT"
            else:
                st = "AMBIGUOUS" if ("AMBIGUOUS" in states or len(vals) > 1) else "GROUNDED"
            m[f] = {"values": vals, "state": st}
        merged.append(m)
    return merged


def structure(pid):
    with open(os.path.join(OUT_DIR, f"{pid}.json"), encoding="utf-8") as fh:
        items = json.load(fh)
    lines = {f"L{i}": d for i, d in enumerate(items)}
    prompt = "\n".join(f'{k}: {d["text"]}' for k, d in lines.items())
    resp = ollama.chat(
        model=MODEL, format="json", options={"temperature": 0},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    )
    try:
        raw = json.loads(resp["message"]["content"])
    except Exception:
        raw = {}
    entries, rejected, covered = [], [], set()
    for m in raw.get("medications", []):
        ids = m.get("line_ids") or []
        if isinstance(ids, str):
            ids = [ids]
        ids = [i for i in ids if i in lines]
        covered.update(ids)
        src = " ".join(lines[i]["text"] for i in ids)
        ns = norm(src)
        min_score = min((lines[i]["score"] for i in ids), default=0.0)
        e = {"line_ids": ids, "source_text": src, "min_ocr_score": min_score}
        for f in FIELDS:
            v = m.get(f)
            if v in (None, "", "null"):
                e[f] = {"value": None, "state": "NOT_PRESENT"}
                continue
            nv = norm(str(v))
            grounded = bool(nv) and (nv in ns or fuzz.partial_ratio(nv, ns) >= 85)
            if grounded:
                e[f] = {"value": v, "state": "GROUNDED" if min_score >= 0.8 else "AMBIGUOUS"}
            else:
                e[f] = {"value": None, "state": "AMBIGUOUS"}
                rejected.append({"field": f, "value": v, "lines": ids, "reason": "not found in cited OCR lines"})
        entries.append(e)
    uncovered = [
        {"line_id": k, "text": d["text"], "score": d["score"]}
        for k, d in lines.items() if is_candidate(d["text"]) and k not in covered
    ]
    return {
        "image": pid,
        "review_required": True,
        "medications": merge(entries),
        "unparsed_candidate_lines": uncovered,
        "rejected": rejected,
        "note": "GROUNDED = text present in OCR with score>=0.8. Provisional, NOT calibrated.",
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["all"]:
        args = sorted((f[:-5] for f in os.listdir(OUT_DIR) if f.endswith(".json")),
                      key=lambda s: int(s) if s.isdigit() else 0)
    for pid in args:
        dest = os.path.join(RES_DIR, f"{pid}.json")
        if len(args) > 3 and os.path.exists(dest):
            continue
        result = structure(pid)
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        print(f'{pid}: {len(result["medications"])} meds | {len(result["rejected"])} rejected | '
              f'{len(result["unparsed_candidate_lines"])} unparsed candidate lines')
        if len(args) <= 3:
            print(json.dumps(result, ensure_ascii=False, indent=1))