from __future__ import annotations

import numpy as np

from stream_media_viewer.detect.blur import apply_marks, gaussian_region
from stream_media_viewer.detect.faces import detect_face_boxes
from stream_media_viewer.detect.text_regions import detect_text_boxes


def protect_frame(
    bgr: np.ndarray,
    *,
    face_blur: bool,
    text_blur: bool,
    marks: list[dict],
    strength: int,
) -> tuple[np.ndarray, bool, bool]:
    out = bgr.copy()
    faces = detect_face_boxes(out) if face_blur else []
    texts = detect_text_boxes(out) if text_blur else []
    for box in faces + texts:
        gaussian_region(out, box, strength)
    apply_marks(out, marks, strength)
    return out, bool(faces), bool(texts)
