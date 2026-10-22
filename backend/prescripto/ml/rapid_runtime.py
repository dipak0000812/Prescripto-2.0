"""
RapidOCR Runtime — Real OCR perception engine for prescription images.

Uses rapidocr-onnxruntime (ONNX-based PaddleOCR models) to perform actual
text detection and recognition on uploaded prescription images.

Implements the same recognize_document(image_bytes) -> List[OCRLine] interface
as MockModelRuntime and RemoteMLClient so the worker pipeline requires zero
changes when switching runtime modes.
"""
from __future__ import annotations

import logging
import time
from io import BytesIO
from statistics import median
from typing import Any, List, Optional

from prescripto.ml.runtime import OCRLine

logger = logging.getLogger("prescripto.ml.rapid_runtime")


class RapidOCRRuntime:
    """
    Production OCR runtime backed by rapidocr-onnxruntime.

    Runs entirely on CPU via ONNX Runtime — no PaddlePaddle or PyTorch needed.
    Bundled models: PP-OCRv4 detection + recognition (English).
    """

    def __init__(self) -> None:
        self._engine: Any = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
            except ImportError as error:
                raise RuntimeError(
                    "rapidocr-onnxruntime is required for the RapidOCR runtime; "
                    "install it with: pip install rapidocr-onnxruntime"
                ) from error
            self._engine = RapidOCR()
            logger.info("RapidOCR engine initialised (ONNX CPU)")
        return self._engine

    def recognize_document(self, image_bytes: bytes) -> List[OCRLine]:
        """
        Accepts raw image bytes, runs text detection + recognition,
        and returns grouped OCRLine objects compatible with the pipeline.
        """
        if not image_bytes:
            raise ValueError("RapidOCR requires non-empty image bytes")

        try:
            import numpy as np
            from PIL import Image
        except ImportError as error:
            raise RuntimeError("Pillow and NumPy are required by the OCR runtime") from error

        # Decode image
        with Image.open(BytesIO(image_bytes)) as source:
            img_array = np.asarray(source.convert("RGB"))

        t_start = time.perf_counter()
        engine = self._get_engine()
        result, elapse = engine(img_array)
        latency_ms = int((time.perf_counter() - t_start) * 1000)
        logger.info("RapidOCR inference completed in %d ms", latency_ms)

        if not result:
            return []

        # result is List[Tuple[bbox_points, text, score]]
        # bbox_points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        raw_items: list[tuple[str, float, tuple[float, float, float, float]]] = []
        for item in result:
            bbox_points = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            text = str(item[1])
            score = float(item[2]) if item[2] is not None else 0.0

            # Convert polygon to rectangle (x_min, y_min, x_max, y_max)
            xs = [float(p[0]) for p in bbox_points]
            ys = [float(p[1]) for p in bbox_points]
            box = (min(xs), min(ys), max(xs), max(ys))
            raw_items.append((text, score, box))

        # Group into reading lines by y-centre proximity (same logic as PaddleOCRRuntime)
        return self._group_lines(raw_items)

    @staticmethod
    def _group_lines(
        items: list[tuple[str, float, tuple[float, float, float, float]]],
    ) -> List[OCRLine]:
        """Groups word-level detections into reading lines by y-centre proximity."""
        sorted_items = sorted(
            items,
            key=lambda item: ((item[2][1] + item[2][3]) / 2, item[2][0]),
        )

        heights = [max(1.0, box[3] - box[1]) for _, _, box in sorted_items]
        line_tolerance = max(4.0, median(heights) * 0.6) if heights else 4.0

        groups: list[list[tuple[str, float, tuple[float, float, float, float]]]] = []
        for item in sorted_items:
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

        lines: List[OCRLine] = []
        for line_index, group in enumerate(groups):
            group.sort(key=lambda item: item[2][0])
            x_min = min(item[2][0] for item in group)
            y_min = min(item[2][1] for item in group)
            x_max = max(item[2][2] for item in group)
            y_max = max(item[2][3] for item in group)
            line_scores = [score for _, score, _ in group if score > 0]
            lines.append(
                OCRLine(
                    line_index=line_index,
                    text=" ".join(text.strip() for text, _, _ in group if text.strip()),
                    raw_score=min(line_scores) if line_scores else None,
                    box=(x_min, y_min, x_max, y_max),
                )
            )
        return lines
