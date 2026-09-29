from __future__ import annotations

import copy
import threading
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from stream_media_viewer.detect.blur import apply_marks, gaussian_oval, gaussian_region
from stream_media_viewer.detect.faces import FaceHold, detect_face_boxes
from stream_media_viewer.detect.text_regions import detect_text_boxes
from stream_media_viewer.errors import log_exception
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.render.rotate import rotate_bgr
from stream_media_viewer.settings import AppSettings

PROTECT_LOCK = threading.Lock()


@dataclass(frozen=True)
class ProtectSettings:
    """裏の処理を始めた時点の、ぼかしに関わる設定の写し。

    処理の途中で顔ぼかしのオン／オフなどを変えても、始めたときの設定で作り切る。
    下準備の鍵は始めたときの設定で作るので、中身も同じ設定でないと
    「顔ぼかしオン」の鍵に素顔の絵が入ってしまう。
    """

    face_blur: bool
    text_blur: bool
    blur_strength: int
    enhance_level: str
    face_pipeline: str
    false_face_hashes: tuple[str, ...]

    @classmethod
    def of(cls, settings: AppSettings | ProtectSettings) -> ProtectSettings:
        if isinstance(settings, ProtectSettings):
            return settings
        return cls(
            face_blur=bool(settings.face_blur),
            text_blur=bool(settings.text_blur),
            blur_strength=int(settings.blur_strength),
            enhance_level=str(settings.enhance_level),
            face_pipeline=str(settings.face_pipeline),
            false_face_hashes=tuple(settings.all_false_face_hashes()),
        )

    def all_false_face_hashes(self) -> list[str]:
        return list(self.false_face_hashes)


def note_snapshot(note: FileNote) -> FileNote:
    """裏の処理に渡すファイルごとの記録の写し（手動ぼかし・回転・顔を探さない）。"""
    return FileNote(
        marks=copy.deepcopy(list(note.marks)),
        skip_faces=bool(note.skip_faces),
        rotation=int(note.rotation),
    )


def acquire_protect_lock(
    should_stop: Callable[[], bool],
    *,
    timeout: float = 0.05,
) -> bool:
    while True:
        if should_stop():
            return False
        if PROTECT_LOCK.acquire(timeout=timeout):
            return True


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
    still: bool = False,
) -> tuple[np.ndarray, bool, bool]:
    out = bgr.copy()
    if face_blur:
        detected = detect_face_boxes(
            out, false_face_hashes=false_face_hashes, pipeline=pipeline, still=still
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
    still: bool = False,
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
            still=still,
        )
    except Exception as exc:
        log_exception(exc)
        return None, False, False


def protect_for_note(
    bgr: np.ndarray,
    settings: AppSettings | ProtectSettings,
    note: FileNote,
    *,
    face_hold: FaceHold | None = None,
    still: bool = False,
) -> tuple[np.ndarray | None, bool, bool]:
    """still=True は写真。時間をかけて小さい顔・横倒しの顔も探す（動画のコマは False）。"""
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
        still=still,
    )
