"""PaddleOCR adapter for uploaded prescription images."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from statistics import median
from typing import Any, Callable


@dataclass(frozen=True)
class OCRLine:
    line_index: int
    text: str
    raw_score: float | None
    box: tuple[float, float, float, float]


class PaddleOCRRuntime:
    """Run the PaddleOCR page pipeline and group word boxes into reading lines."""

    def __init__(self, device: str = "cpu", ocr: Any | None = None) -> None:
        self.device = device
        self._ocr = ocr

    def _get_ocr(self) -> Any:
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as error:
                raise RuntimeError(
                    "OCR runtime dependencies are missing; install the 'ocr' extra."
                ) from error

            self._ocr = PaddleOCR(
                device=self.device,
                ocr_version="PP-OCRv6",
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        return self._ocr

    @staticmethod
    def _payload(result: Any) -> dict[str, Any]:
        payload = getattr(result, "json", result)
        if callable(payload):
            payload = payload()
        if not isinstance(payload, dict):
            raise ValueError("PaddleOCR returned an unsupported result object")
        nested = payload.get("res", payload)
        if not isinstance(nested, dict):
            raise ValueError("PaddleOCR result is missing its structured payload")
        return nested

    @staticmethod
    def _boxes_to_rectangles(polygons: Any, count: int) -> list[tuple[float, float, float, float]]:
        rectangles: list[tuple[float, float, float, float]] = []
        for index in range(count):
            if polygons is None or index >= len(polygons):
                rectangles.append((0.0, float(index), 1.0, float(index + 1)))
                continue
            points = polygons[index]
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
            rectangles.append((min(xs), min(ys), max(xs), max(ys)))
        return rectangles

    @staticmethod
    def _group_lines(
        texts: list[str], scores: list[float | None], boxes: list[tuple[float, float, float, float]]
    ) -> list[OCRLine]:
        items = sorted(
            zip(texts, scores, boxes),
            key=lambda item: ((item[2][1] + item[2][3]) / 2, item[2][0]),
        )
        heights = [max(1.0, box[3] - box[1]) for _, _, box in items]
        line_tolerance = max(4.0, median(heights) * 0.6) if heights else 4.0
        groups: list[list[tuple[str, float | None, tuple[float, float, float, float]]]] = []

        for item in items:
            center_y = (item[2][1] + item[2][3]) / 2
            if not groups:
                groups.append([item])
                continue
            previous_centers = [(entry[2][1] + entry[2][3]) / 2 for entry in groups[-1]]
            group_center = sum(previous_centers) / len(previous_centers)
            if abs(center_y - group_center) <= line_tolerance:
                groups[-1].append(item)
            else:
                groups.append([item])

        lines: list[OCRLine] = []
        for line_index, group in enumerate(groups):
            group.sort(key=lambda item: item[2][0])
            x_min = min(item[2][0] for item in group)
            y_min = min(item[2][1] for item in group)
            x_max = max(item[2][2] for item in group)
            y_max = max(item[2][3] for item in group)
            line_scores = [score for _, score, _ in group if score is not None]
            lines.append(
                OCRLine(
                    line_index=line_index,
                    text=" ".join(text.strip() for text, _, _ in group if text.strip()),
                    raw_score=min(line_scores) if line_scores else None,
                    box=(x_min, y_min, x_max, y_max),
                )
            )
        return lines

    def recognize_document(self, image_bytes: bytes) -> list[OCRLine]:
        try:
            import numpy as np
            from PIL import Image
        except ImportError as error:
            raise RuntimeError("Pillow and NumPy are required by the OCR extra") from error

        with Image.open(BytesIO(image_bytes)) as source:
            image = np.asarray(source.convert("RGB"))

        predictions = self._get_ocr().predict(image)
        texts: list[str] = []
        scores: list[float | None] = []
        polygons: Any = None
        for prediction in predictions:
            payload = self._payload(prediction)
            texts.extend(str(text) for text in payload.get("rec_texts", []))
            scores.extend(
                float(score) if score is not None else None
                for score in payload.get("rec_scores", [])
            )
            if polygons is None:
                polygons = payload.get("dt_polys")

        if len(scores) < len(texts):
            scores.extend([None] * (len(texts) - len(scores)))
        boxes = self._boxes_to_rectangles(polygons, len(texts))
        return self._group_lines(texts, scores[: len(texts)], boxes)
