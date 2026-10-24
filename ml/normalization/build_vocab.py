import csv, os, re

RX = r"C:\Users\Admin\Desktop\prescription_project\data\RxHandBD-ML\RxHandBD-ML"
OUT = r"C:\Users\Admin\Desktop\Prescripto-2.0\data\vocab"
EXTRA = os.path.join(OUT, "extra_names.txt")  # optional: one name per line (team list / reviewer-confirmed)
os.makedirs(OUT, exist_ok=True)

names = {}
def add(raw, source):
    t = re.sub(r"\s+", " ", str(raw).strip())
    if len(t) < 4 or not re.search(r"[A-Za-z]{4}", t) or "?" in t:
        return
    names.setdefault(t.lower(), (t, source))

for fname in ("Train_Label.csv", "Test_Label.csv"):
    with open(os.path.join(RX, fname), encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            add(row.get("Text", ""), "RxHandBD")
if os.path.exists(EXTRA):
    with open(EXTRA, encoding="utf-8") as fh:
        for line in fh:
            add(line, "EXTRA")

with open(os.path.join(OUT, "medicine_vocab.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["name", "source", "source_class", "verification_status"])
    for t, src in sorted(names.values(), key=lambda x: x[0].lower()):
        w.writerow([t, src, "RESEARCH_VOCABULARY", "UNVERIFIED"])
print(len(names), "names written")