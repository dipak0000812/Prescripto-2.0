import json, os, re
from rapidfuzz import fuzz

ROOT = r"C:\Users\Admin\Desktop\Prescripto-2.0"
T = 80
PREFIX = r"^(tab|tas|cap|syp|inj|t|pb)\b[\.\s]*"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(PREFIX, "", s.strip(), flags=re.I).lower())


def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


def hit(d, n):
    return fuzz.ratio(d, n) >= T or (len(n) >= 5 and fuzz.partial_ratio(d, n) >= T)


labels = {str(r["image"]): [norm(d) for d in r["drugs"]]
          for r in load(os.path.join(ROOT, r"data\labels\drug_labels.json"))}
G = ("both_readers", "vlm_only", "paddle_only")
stat = {g: [0, 0] for g in G}
found = {g: 0 for g in G}
total = any_found = 0
for img, drugs in labels.items():
    names = []
    for m in load(os.path.join(ROOT, rf"outputs\final\{img}.json"))["medications"]:
        n = norm(m["medication_name"]["raw_text"])
        if len(n) >= 3:
            names.append((n, m["medication_name"]["reader_agreement"]))
    for n, g in names:
        stat[g][0] += 1
        stat[g][1] += any(hit(d, n) for d in drugs)
    for d in drugs:
        total += 1
        gs = {g for n, g in names if hit(d, n)}
        any_found += bool(gs)
        for g in gs:
            found[g] += 1

print(f"{len(labels)} labeled images, {total} labeled drugs\n")
for g in G:
    n, c = stat[g]
    print(f"{g:13s}: {n:3d} names, {c:3d} correct = {c/max(n,1):.0%} | labeled drugs found: {found[g]}")
print(f"\nRecall if reviewer sees ALL names        : {any_found}/{total} = {any_found/total:.0%}")
print(f"Recall from standard-priority names only : {found['both_readers']}/{total} = {found['both_readers']/total:.0%}")