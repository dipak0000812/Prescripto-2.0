import torch
import os
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

DATA_DIR = r"C:\Users\Admin\Desktop\prescripto data"
CROP_DIR = r"C:\Users\Admin\Desktop\Prescripto-2.0\outputs\crops"
N_IMAGES = 5
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")

os.makedirs(CROP_DIR, exist_ok=True)
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("khedim/Medical-Prescription-OCR").to(device).eval()
print("Model loaded. Vocab sizes -> tokenizer:", len(processor.tokenizer), "| model:", model.config.decoder.vocab_size)
det = PaddleOCR(device="gpu:0")




files = sorted(f for f in os.listdir(DATA_DIR) if f.lower().endswith(EXTS))[:N_IMAGES]
print(f"Running on {len(files)} images, torch device: {device}\n")

for fname in files:
    img = Image.open(os.path.join(DATA_DIR, fname)).convert("RGB")
    result = det.predict(np.array(img))[0]
    print(f"===== {fname} =====")
    for i, (box, paddle_text) in enumerate(zip(result["rec_boxes"], result["rec_texts"])):
        x1, y1, x2, y2 = [int(v) for v in box]
        crop = img.crop((x1, y1, x2, y2))
        crop.save(os.path.join(CROP_DIR, f"{os.path.splitext(fname)[0]}_line{i:02d}.png"))
        pv = processor(images=crop, return_tensors="pt").pixel_values.to(device)
        with torch.no_grad():
            ids = model.generate(pv, max_length=64, num_beams=4)
        khedim_text = processor.batch_decode(ids, skip_special_tokens=True)[0]
        print(f"[{i:02d}] PADDLE: {paddle_text}")
        print(f"     KHEDIM: {khedim_text}")
    print()