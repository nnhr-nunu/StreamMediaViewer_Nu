from __future__ import annotations

import numpy as np

from stream_media_viewer.detect.blur import apply_marks, gaussian_oval, gaussian_region
from stream_media_viewer.detect.faces import detect_face_boxes
from stream_media_viewer.detect.text_regions import detect_text_boxes
from stream_media_viewer.errors import log_exception


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
    for box in faces:
        gaussian_oval(out, box, strength)
    for box in texts:
        gaussian_region(out, box, strength)
    apply_marks(out, marks, strength)
    return out, bool(faces), bool(texts)


def protect_frame_safe(
    bgr: np.ndarray,
    *,
    face_blur: bool,
    text_blur: bool,
    marks: list[dict],
    strength: int,
) -> tuple[np.ndarray | None, bool, bool]:
    if bgr.ndim != 3 or bgr.shape[0] < 2 or bgr.shape[1] < 2 or bgr.shape[2] != 3:
        return None, False, False
    try:
        return protect_frame(
            bgr,
            face_blur=face_blur,
            text_blur=text_blur,
            marks=marks,
            strength=strength,
        )
    except Exception as exc:
        log_exception(exc)
        return None, False, False
