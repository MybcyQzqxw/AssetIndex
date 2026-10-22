"""OCR wrapper (RapidOCR / ONNX, fully offline) that reads the asset number from a label photo."""
from __future__ import annotations

import math
from typing import List, Optional

import numpy as np
from PIL import Image, ImageOps

from .asset_parser import parse_asset_number

try:  # HEIC/HEIF support is optional.
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass

# (rotation in degrees, longest side in px) tried in order until a number is found.
_ATTEMPTS = ((0, 1600), (0, 2600), (90, 1600), (270, 1600))

# Orientation detection: working size, "already upright" score, and the margin a rotated
# reading must win by before the photo is turned.
_ORIENT_SIZE = 1000
_ORIENT_CONFIDENT = 30.0
_ORIENT_MIN_SCORE = 6.0
_ORIENT_RATIO = 3.0


def open_image(path: str) -> Image.Image:
    """Open an image honouring EXIF orientation, converted to RGB."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return im.convert("RGB")


class AssetNumberReader:
    def __init__(self) -> None:
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
        return self._engine

    def _ocr_lines(self, image: Image.Image) -> List[str]:
        arr = np.ascontiguousarray(np.asarray(image)[:, :, ::-1])  # RGB -> BGR
        result, _ = self._get_engine()(arr)
        if not result:
            return []
        # Reading order: top to bottom, then left to right.
        result = sorted(result, key=lambda r: (min(p[1] for p in r[0]), min(p[0] for p in r[0])))
        return [r[1] for r in result]

    def _text_score(self, image: Image.Image) -> float:
        """Confidence-weighted amount of *horizontal*, correctly read text in ``image``.

        The classifier is disabled and vertical boxes are ignored on purpose: RapidOCR silently
        rotates tall crops, which would make sideways text look readable.
        """
        arr = np.ascontiguousarray(np.asarray(image)[:, :, ::-1])
        result, _ = self._get_engine()(arr, use_cls=False)
        score = 0.0
        for box, text, conf in result or []:
            width = math.dist(box[0], box[1])
            height = math.dist(box[1], box[2])
            if float(conf) >= 0.6 and width >= 1.2 * height:
                score += len(text.strip()) * float(conf)
        return score

    def detect_rotation(self, path: str) -> int:
        """Degrees to rotate the photo counter-clockwise (0/90/180/270) so its main text is upright."""
        image = open_image(path)
        image.thumbnail((_ORIENT_SIZE, _ORIENT_SIZE), Image.LANCZOS)

        upright = self._text_score(image)
        if upright >= _ORIENT_CONFIDENT:
            return 0

        scores = {0: upright}
        for angle in (180, 90, 270):
            scores[angle] = self._text_score(image.rotate(angle, expand=True))
        best = max(scores, key=scores.get)
        if best != 0 and scores[best] >= _ORIENT_MIN_SCORE and scores[best] >= _ORIENT_RATIO * upright:
            return best
        return 0

    def read(self, path: str) -> Optional[str]:
        """Return the asset number found on the label in ``path`` or ``None``."""
        base = open_image(path)
        for rotation, longest in _ATTEMPTS:
            img = base.rotate(rotation, expand=True) if rotation else base
            if max(img.size) > longest:
                scale = longest / max(img.size)
                img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
            number = parse_asset_number(self._ocr_lines(img))
            if number:
                return number
        return None
