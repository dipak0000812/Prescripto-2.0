import json, sys, os

OUT_DIR = r"C:\Users\Admin\Desktop\Prescripto-2.0\outputs\ocr_paddle"
for pid in sys.argv[1:]:
    with open(os.path.join(OUT_DIR, f"{pid}.json"), encoding="utf-8") as fh:
        items = json.load(fh)
    print(f"\n===== {pid} ({len(items)} lines) =====")
    for d in items:
        flag = " ?" if d["score"] < 0.8 else ""
        print(f'{d["score"]:.2f}  {d["text"]}{flag}')