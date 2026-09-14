from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QObject, QTimer, QUrl, Signal

from stream_media_viewer.library.scan import PREVIEW_MAX_SIDE, video_header_ok

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:  # pragma: no cover
    QAudioOutput = None  # type: ignore[misc, assignment]
    QMediaPlayer = None  # type: ignore[misc, assignment]


def _limit_frame(frame: np.ndarray) -> np.ndarray:
    height, width = frame.shape[:2]
    long_edge = max(height, width)
    if long_edge <= PREVIEW_MAX_SIDE:
        return frame
    scale = PREVIEW_MAX_SIDE / long_edge
    return cv2.resize(
        frame,
        (max(1, int(width * scale)), max(1, int(height * scale))),
        interpolation=cv2.INTER_AREA,
    )


class VideoPlayer(QObject):
    frame_ready = Signal(object)
    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._cap: cv2.VideoCapture | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._tick)
        self._interval_ms = 33
        self.in_ms = 0
        self.out_ms: int | None = None
        self.loop = False
        self.playing = False
        self.audio_enabled = False
        self._protect: Callable[[np.ndarray], np.ndarray] | None = None
        self.last_raw: np.ndarray | None = None
        self._last_ok: np.ndarray | None = None
        self._audio = None
        self._sink = None
        self._cache_dir: Path | None = None
        self._cache_index = 0
        self._cache_fps = 30.0
        self._source_path = ""
        if QMediaPlayer is not None and QAudioOutput is not None:
            self._sink = QAudioOutput(self)
            self._audio = QMediaPlayer(self)
            self._audio.setAudioOutput(self._sink)
            self._sink.setVolume(0.0)

    def open(self, path: str) -> float:
        self.close()
        self._source_path = path
        self._cache_dir = None
        if not video_header_ok(Path(path)):
            return 0.0
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = None
            return 0.0
        if self._audio is not None:
            self._audio.setSource(QUrl.fromLocalFile(path))
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 30.0)
        if fps <= 1:
            fps = 30.0
        self._interval_ms = max(16, int(1000 / fps))
        return fps

    def duration_ms(self) -> int:
        if not self._cap:
            return 0
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 30.0)
        frames = float(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0:
            return 0
        return int(1000 * frames / fps)

    def position_ms(self) -> int:
        if self._cache_dir is not None:
            return int(self.in_ms + self._cache_index * (1000 / max(1.0, self._cache_fps)))
        if not self._cap:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_POS_MSEC) or 0)

    def set_cache(self, folder: Path | None, fps: float) -> None:
        self._cache_dir = folder
        self._cache_fps = fps if fps > 1 else 30.0
        self._cache_index = 0

    def set_protect(self, fn: Callable[[np.ndarray], np.ndarray] | None) -> None:
        self._protect = fn

    def set_audio_enabled(self, enabled: bool) -> None:
        self.audio_enabled = bool(enabled)
        if self._audio is None or self._sink is None:
            return
        if self.audio_enabled and self.playing:
            self._sync_audio_clock()
            self._audio.play()
            return
        self._sink.setVolume(0.0)
        self._audio.pause()

    def seek_ms(self, ms: int) -> np.ndarray | None:
        if not self._cap:
            return None
        target = max(0, ms)
        self._cap.set(cv2.CAP_PROP_POS_MSEC, target)
        if self._audio is not None:
            self._audio.setPosition(target)
        ok, frame = self._cap.read()
        if not ok:
            return None
        return self._apply(_limit_frame(frame))

    def play(self) -> None:
        self.playing = True
        self._sync_audio_clock()
        if self._audio is not None and self.audio_enabled:
            self._audio.play()
        elif self._audio is not None:
            self._audio.pause()
            if self._sink is not None:
                self._sink.setVolume(0.0)
        if self._cache_dir is not None:
            self._cache_index = 0
            self._interval_ms = max(16, int(1000 / self._cache_fps))
        self._timer.start(self._interval_ms)

    def pause(self) -> None:
        self.playing = False
        self._timer.stop()
        if self._audio is not None:
            self._audio.pause()

    def close(self) -> None:
        self.pause()
        self._last_ok = None
        self.last_raw = None
        self._protect = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._audio is not None:
            self._audio.stop()
            self._audio.setSource(QUrl())

    def _apply(self, frame: np.ndarray) -> np.ndarray | None:
        self.last_raw = frame
        if self._protect is None:
            self._last_ok = frame
            return frame
        try:
            protected = self._protect(frame)
        except Exception:
            return self._last_ok
        self._last_ok = protected
        return protected

    def _sync_audio_clock(self) -> None:
        if self._audio is None or self._sink is None:
            return
        pos = self.position_ms()
        if self.audio_enabled:
            self._sink.setVolume(1.0)
            if abs(self._audio.position() - pos) > 80:
                self._audio.setPosition(pos)
        else:
            self._sink.setVolume(0.0)
            self._audio.pause()

    def _continue(self) -> None:
        if self.playing:
            self._timer.start(self._interval_ms)

    def _tick(self) -> None:
        if self._cache_dir is not None:
            self._tick_cache()
            return
        if not self._cap or not self.playing:
            return
        pos = self.position_ms()
        if self.out_ms is not None and pos >= self.out_ms:
            if self.loop:
                self.seek_ms(self.in_ms)
                self._sync_audio_clock()
                if self._audio is not None and self.audio_enabled:
                    self._audio.play()
                self._continue()
                return
            self.pause()
            self.finished.emit()
            return
        ok, frame = self._cap.read()
        if not ok:
            if self.loop:
                self.seek_ms(self.in_ms)
                self._sync_audio_clock()
                if self._audio is not None and self.audio_enabled:
                    self._audio.play()
                self._continue()
                return
            self.pause()
            self.finished.emit()
            return
        protected = self._apply(_limit_frame(frame))
        if protected is None:
            self.pause()
            return
        self._sync_audio_clock()
        self.frame_ready.emit(protected)
        self._continue()

    def _tick_cache(self) -> None:
        if not self.playing or self._cache_dir is None:
            return
        frame_path = self._cache_dir / f"{self._cache_index:06d}.jpg"
        if not frame_path.is_file():
            if self.loop:
                self._cache_index = 0
                self._sync_audio_clock()
                if self._audio is not None and self.audio_enabled:
                    self._audio.setPosition(self.in_ms)
                    self._audio.play()
                self._continue()
                return
            self.pause()
            self.finished.emit()
            return
        frame = cv2.imread(str(frame_path))
        if frame is None:
            self.pause()
            self.finished.emit()
            return
        self._last_ok = frame
        self.frame_ready.emit(frame)
        self._sync_audio_clock()
        self._cache_index += 1
        self._continue()
