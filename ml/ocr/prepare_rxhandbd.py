from pathlib import Path

DATASET_DIR = Path(
    r"C:\Users\Admin\Desktop\prescription_project\data\RxHandBD-ML\RxHandBD-ML"
)

OUTPUT_DIR = Path("ml/ocr/rxhandbd")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def convert(input_file, output_file):
    count = 0

    with open(input_file, "r", encoding="utf-8") as src, \
         open(output_file, "w", encoding="utf-8") as dst:

        for line in src:
            line = line.strip()

            if not line:
                continue

            image_path, label = line.split(None, 1)

            # PaddleOCR format:
            # image_path<TAB>label
            dst.write(f"{image_path}\t{label}\n")
            count += 1

    return count


train_count = convert(
    DATASET_DIR / "train_rec.txt",
    OUTPUT_DIR / "train.txt"
)

val_count = convert(
    DATASET_DIR / "val_rec.txt",
    OUTPUT_DIR / "val.txt"
)

print(f"Train samples converted: {train_count}")
print(f"Validation samples converted: {val_count}")
print(f"Output directory: {OUTPUT_DIR.resolve()}")