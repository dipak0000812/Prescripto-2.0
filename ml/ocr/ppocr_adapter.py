import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from .model_runtime import ModelRuntime


class PPOCRAdapter(ModelRuntime):
    """
    PaddleOCR runs detection + recognition together internally (predict()).
    Images are loaded via PIL first (handles mislabeled formats like GIF-as-.jpg)
    then converted to RGB numpy arrays before passing to PaddleOCR.
    """

    def __init__(self, device: str = "gpu:0"):
        self._ocr = PaddleOCR(device=device)
        self._cache = {}

    def _load_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        return np.array(img)

    def detect_regions(self, image):
        img_array = self._load_image(image)
        results = self._ocr.predict(img_array)
        regions = []
        for result in results:
            for i, (text, score) in enumerate(zip(result["rec_texts"], result["rec_scores"])):
                region_id = f"region_{i}"
                self._cache[region_id] = (text, score)
                regions.append(region_id)
        return regions

    def recognize_line(self, image):
        if image not in self._cache:
            raise ValueError(f"Unknown region: {image}. Call detect_regions() first.")
        return self._cache[image]

    @property
    def model_version_id(self):
        return "ppocrv6"