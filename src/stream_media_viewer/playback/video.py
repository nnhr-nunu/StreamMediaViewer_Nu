from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal


class VideoPlayer(QObject):
    frame_ready = Signal(object)
    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._cap: cv2.VideoCapture | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.in_ms = 0
        self.out_ms: int | None = None
        self.loop = False
        self.playing = False
        self._protect = None
        self._last_ok: np.ndarray | None = None

    def open(self, path: str) -> float:
        self.close()
        self._cap = cv2.VideoCapture(path)
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 30.0)
        return fps if fps > 1 else 30.0

    def duration_ms(self) -> int:
        if not self._cap:
            return 0
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 30.0)
        frames = float(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0:
            return 0
        return int(1000 * frames / fps)

    def set_protect(self, fn) -> None:
        self._protect = fn

    def seek_ms(self, ms: int) -> np.ndarray | None:
        if not self._cap:
            return None
        self._cap.set(cv2.CAP_PROP_POS_MSEC, max(0, ms))
        ok, frame = self._cap.read()
        if not ok:
            return None
        return self._apply(frame)

    def play(self) -> None:
        self.playing = True
        self._timer.start(1)

    def pause(self) -> None:
        self.playing = False
        self._timer.stop()

    def close(self) -> None:
        self.pause()
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _apply(self, frame: np.ndarray) -> np.ndarray:
        if self._protect is None:
            self._last_ok = frame
            return frame
        protected = self._protect(frame)
        self._last_ok = protected
        return protected

    def _tick(self) -> None:
        if not self._cap or not self.playing:
            return
        pos = int(self._cap.get(cv2.CAP_PROP_POS_MSEC) or 0)
        if self.out_ms is not None and pos >= self.out_ms:
            if self.loop:
                self._cap.set(cv2.CAP_PROP_POS_MSEC, self.in_ms)
            else:
                self.pause()
                self.finished.emit()
                return
        ok, frame = self._cap.read()
        if not ok:
            if self.loop:
                self._cap.set(cv2.CAP_PROP_POS_MSEC, self.in_ms)
                return
            self.pause()
            self.finished.emit()
            return
        protected = self._apply(frame)
        self.frame_ready.emit(protected)
