from __future__ import annotations

import numpy as np

from stream_media_viewer.detect.blur import apply_marks, gaussian_oval, gaussian_region
from stream_media_viewer.detect.faces import FaceHold, detect_face_boxes
from stream_media_viewer.detect.text_regions import detect_text_boxes
from stream_media_viewer.errors import log_exception
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.render.rotate import rotate_bgr
from stream_media_viewer.settings import AppSettings


def protect_frame(
    bgr: np.ndarray,
    *,
    face_blur: bool,
    text_blur: bool,
    marks: list[dict],
    strength: int,
    false_face_hashes: list[str] | None = None,
    pipeline: str | None = None,
    face_hold: FaceHold | None = None,
) -> tuple[np.ndarray, bool, bool]:
    out = bgr.copy()
    if face_blur:
        detected = detect_face_boxes(
            out, false_face_hashes=false_face_hashes, pipeline=pipeline
        )
        faces = face_hold.step(detected) if face_hold is not None else detected
    else:
        if face_hold is not None:
            face_hold.reset()
        faces = []
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
    false_face_hashes: list[str] | None = None,
    pipeline: str | None = None,
    face_hold: FaceHold | None = None,
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
            false_face_hashes=false_face_hashes,
            pipeline=pipeline,
            face_hold=face_hold,
        )
    except Exception as exc:
        log_exception(exc)
        return None, False, False


def protect_for_note(
    bgr: np.ndarray,
    settings: AppSettings,
    note: FileNote,
    *,
    face_hold: FaceHold | None = None,
) -> tuple[np.ndarray | None, bool, bool]:
    oriented = rotate_bgr(bgr, note.rotation)
    return protect_frame_safe(
        oriented,
        face_blur=settings.face_blur and not note.skip_faces,
        text_blur=settings.text_blur,
        marks=note.marks,
        strength=settings.blur_strength,
        false_face_hashes=settings.all_false_face_hashes(),
        pipeline=settings.face_pipeline,
        face_hold=face_hold,
    )
