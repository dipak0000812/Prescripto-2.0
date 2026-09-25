from paddleocr import PaddleOCR

IMAGE_PATH = r"C:\Users\Admin\Desktop\prescription_project\data\paddleocr_dataset\1_test.jpg"

ocr = PaddleOCR(device="gpu:0")
results = ocr.predict(IMAGE_PATH)

for result in results:
    for text, score in zip(result["rec_texts"], result["rec_scores"]):
        print(f"{score:.3f}  {text}")
