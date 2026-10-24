import numpy as np
from PIL import Image
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

try:
    from .model_runtime import ModelRuntime
except (ImportError, ValueError):
    from model_runtime import ModelRuntime


class PPOCRAdapter(ModelRuntime):
    """
    PaddleOCR runs detection + recognition together internally (predict()).
    Images are loaded via PIL first (handles mislabeled formats like GIF-as-.jpg)
    then converted to RGB numpy arrays before passing to PaddleOCR.
    Seamlessly falls back to RapidOCR (ONNX Runtime) when paddleocr is not installed.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._cache = {}
        if HAS_PADDLE:
            self._ocr = PaddleOCR(device=device)
            self._mode = "paddle"
        else:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr = RapidOCR()
            self._mode = "rapidocr"

    def _load_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        return np.array(img)

    def detect_regions(self, image):
        img_array = self._load_image(image)
        regions = []
        if self._mode == "paddle":
            results = self._ocr.predict(img_array)
            for result in results:
                for i, (text, score) in enumerate(zip(result.get("rec_texts", []), result.get("rec_scores", []))):
                    region_id = f"region_{i}"
                    self._cache[region_id] = (text, float(score))
                    regions.append(region_id)
        else:
            results, _ = self._ocr(img_array)
            if results:
                for i, item in enumerate(results):
                    text = str(item[1])
                    score = float(item[2]) if item[2] is not None else 0.0
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