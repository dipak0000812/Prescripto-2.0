import json, os, sys

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
SRC = os.path.join(ROOT, r"outputs\final")
OUT = os.path.join(ROOT, r"outputs\api")
os.makedirs(OUT, exist_ok=True)

FIELDS = ["name", "strength", "dose", "unit", "frequency", "route", "duration", "instructions"]
DETAIL_FIELDS = ["strength", "dose", "frequency", "route", "duration", "instructions"]
VOCAB = "RxHandBD labels (RESEARCH_VOCABULARY, UNVERIFIED)"
MODELS = {"detector_recognizer": "PP-OCRv6 medium (PaddleOCR 3.x)",
          "vision_reader": "qwen2.5vl:7b (Ollama, local)",
          "text_structuring": "qwen2.5:7b-instruct (Ollama, local)"}


def convert(pid):
    with open(os.path.join(SRC, f"{pid}.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    rows, cands, reasons = [], [], ["UNCALIBRATED_CONFIDENCE_DEMO_MODE"]
    for i, m in enumerate(src["medications"]):
        n = m["medication_name"]
        det = m.get("details_from_paddle_text") or {}
        values = {"name": n["raw_text"], "unit": None}
        for f in DETAIL_FIELDS:
            vals = det.get(f) or []
            values[f] = " / ".join(str(v) for v in vals) if vals else None
        row = {"line_index": i}
        for f in FIELDS:
            row[f"{f}_raw"] = values.get(f)
            row[f"{f}_state"] = "AMBIGUOUS"
            row[f"{f}_confidence"] = None
        row["evidence"] = {"reader_agreement": n["reader_agreement"],
                           "review_priority": n["review_priority"]}
        rows.append(row)
        if n["reader_agreement"] != "both_readers":
            reasons.append(f"NAME_SINGLE_READER:line_{i}:{n['reader_agreement']}")
        if not n.get("vocab_candidates"):
            reasons.append(f"NO_VOCAB_CANDIDATE:line_{i}")
        for c in n.get("vocab_candidates", []):
            cands.append({"line_index": i, "extracted_text": n["raw_text"],
                          "candidate_name": c["name"], "candidate_score": c["score"],
                          "matching_strategy": "FUZZY_LEVENSHTEIN", "source_vocabulary": VOCAB,
                          "resolved_medication_id": None, "resolution_status": "UNRESOLVED"})
    if not rows:
        reasons.append("NO_MEDICATION_DETECTED")
    return {"prescription_id": pid, "pipeline_version": "ml-demo-0.1",
            "mode": "RESEARCH_DEMO_UNCALIBRATED", "models": MODELS,
            "review_required": True, "review_reasons": reasons,
            "prescription_medications": rows, "medication_candidates": cands}


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["all"] or not args:
        args = sorted((f[:-5] for f in os.listdir(SRC) if f.endswith(".json")),
                      key=lambda s: int(s) if s.isdigit() else 0)
    n_rows = n_cands = 0
    for pid in args:
        res = convert(pid)
        n_rows += len(res["prescription_medications"])
        n_cands += len(res["medication_candidates"])
        with open(os.path.join(OUT, f"{pid}.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
    print(f"{len(args)} prescriptions -> {OUT}\n{n_rows} medication rows, {n_cands} vocab candidate rows")