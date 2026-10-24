import json, os, re
from rapidfuzz import fuzz

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
T = 80


def norm(s):
    s = re.sub(r"^(tab|tas|cap|syp|inj|t|pb)\b[\.\s]*", "", s.strip(), flags=re.I)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


labels = {str(r["image"]): [norm(d) for d in r["drugs"]]
          for r in load(os.path.join(ROOT, r"data\labels\drug_labels.json"))}

tab = {"corr_right": 0, "corr_wrong": 0, "solo_right": 0, "solo_wrong": 0}
for img, drugs in labels.items():
    paddle = norm(" ".join(d["text"] for d in load(os.path.join(ROOT, rf"outputs\ocr_paddle\{img}.json"))))
    for m in load(os.path.join(ROOT, rf"outputs\vlm\{img}.json"))["medications"]:
        n = norm(m["medication_name"]["values"][0])
        if len(n) < 3:
            continue
        right = any(fuzz.ratio(d, n) >= T or (len(n) >= 5 and fuzz.partial_ratio(d, n) >= T) for d in drugs)
        corr = len(n) >= 4 and fuzz.partial_ratio(n, paddle) >= T
        tab[("corr_" if corr else "solo_") + ("right" if right else "wrong")] += 1

cr, cw, sr, sw = tab["corr_right"], tab["corr_wrong"], tab["solo_right"], tab["solo_wrong"]
print(tab)
print(f"VLM name ALSO in Paddle text : {cr+cw} names, {cr} correct = {cr/max(cr+cw,1):.0%}")
print(f"VLM name ONLY from the VLM   : {sr+sw} names, {sr} correct = {sr/max(sr+sw,1):.0%}")