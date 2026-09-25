from paddleocr import PaddleOCR
from .model_runtime import ModelRuntime


class PPOCRAdapter(ModelRuntime):
    """
    PaddleOCR runs detection + recognition together internally (predict()).
    To honor the ModelRuntime interface, detect_regions() runs the full
    pipeline once and caches per-region results; recognize_line() then
    returns the cached result for that region rather than re-running OCR.
    """

    def __init__(self, device: str = "gpu:0"):
        self._ocr = PaddleOCR(device=device)
        self._cache = {}

    def detect_regions(self, image):
        results = self._ocr.predict(image)
        regions = []
        for result in results:
            for i, (text, score) in enumerate(zip(result["rec_texts"], result["rec_scores"])):
                region_id = f"region_{i}"
                self._cache[region_id] = (text, score)
                regions.append(region_id)
        return regions

    def recognize_line(self, image):
        # image here is actually a region_id from detect_regions(),
        # since recognition already happened during detection.
        if image not in self._cache:
            raise ValueError(f"Unknown region: {image}. Call detect_regions() first.")
        return self._cache[image]

    @property
    def model_version_id(self):
        return "ppocrv6"