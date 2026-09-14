"""確認用の写真読み込み。操作画面は止めない。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal

from stream_media_viewer.detect.protect import PROTECT_LOCK, protect_for_note
from stream_media_viewer.errors import log_exception
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.library.scan import load_rgb_image
from stream_media_viewer.render.canvas import rgb_to_bgr
from stream_media_viewer.render.enhance import enhance_bgr
from stream_media_viewer.settings import AppSettings


class ImageLoadWorker(QThread):
    loaded = Signal(object, int)
    failed = Signal(int)

    def __init__(self, path: Path, seq: int) -> None:
        super().__init__()
        self._path = path
        self._seq = seq

    def run(self) -> None:
        try:
            if self.isInterruptionRequested():
                return
            image = load_rgb_image(self._path)
            if self.isInterruptionRequested():
                return
            if image is None:
                self.failed.emit(self._seq)
                return
            bgr = rgb_to_bgr(np.array(image))
            self.loaded.emit(bgr, self._seq)
        except Exception as exc:
            log_exception(exc)
            if not self.isInterruptionRequested():
                self.failed.emit(self._seq)


class PrefetchWorker(QThread):
    ready = Signal(str, object, bool, bool)

    def __init__(
        self,
        path: Path,
        settings: AppSettings,
        note: FileNote,
        key: str,
    ) -> None:
        super().__init__()
        self._path = path
        self._settings = settings
        self._note = note
        self._key = key

    def run(self) -> None:
        try:
            if self.isInterruptionRequested():
                return
            image = load_rgb_image(self._path)
            if self.isInterruptionRequested() or image is None:
                return
            bgr = rgb_to_bgr(np.array(image))
            with PROTECT_LOCK:
                if self.isInterruptionRequested():
                    return
                out, faces, texts = protect_for_note(bgr, self._settings, self._note)
            if self.isInterruptionRequested() or out is None:
                return
            out = enhance_bgr(out, level=self._settings.enhance_level)
            self.ready.emit(self._key, out, bool(faces), bool(texts))
        except Exception as exc:
            log_exception(exc)
