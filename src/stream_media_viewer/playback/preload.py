from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
from PySide6.QtCore import QThread, Signal

from stream_media_viewer.config import user_config_dir
from stream_media_viewer.detect.protect import protect_frame
from stream_media_viewer.render.canvas import fit_letterbox
from stream_media_viewer.settings import AppSettings


def preload_root() -> Path:
    path = user_config_dir() / "preload"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_key(
    path: Path,
    *,
    in_ms: int,
    out_ms: int | None,
    face_blur: bool,
    text_blur: bool,
    strength: int,
    marks: list[dict[str, Any]],
) -> str:
    stat = path.stat() if path.is_file() else None
    payload = {
        "path": str(path.resolve()) if path.exists() else str(path),
        "mtime": stat.st_mtime if stat else 0,
        "size": stat.st_size if stat else 0,
        "in_ms": in_ms,
        "out_ms": out_ms,
        "face_blur": face_blur,
        "text_blur": text_blur,
        "strength": strength,
        "marks": marks,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def cache_folder(key: str) -> Path:
    return preload_root() / key


def cache_is_ready(key: str) -> bool:
    meta = cache_folder(key) / "meta.json"
    if not meta.is_file():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    count = int(data.get("count") or 0)
    if count < 1:
        return False
    last = cache_folder(key) / f"{count - 1:06d}.jpg"
    return last.is_file()


def read_meta(key: str) -> dict[str, Any]:
    meta = cache_folder(key) / "meta.json"
    return json.loads(meta.read_text(encoding="utf-8"))


class PreloadWorker(QThread):
    progress = Signal(int, int)
    finished_ok = Signal(str)

    def __init__(
        self,
        path: Path,
        key: str,
        settings: AppSettings,
        marks: list[dict[str, Any]],
        in_ms: int,
        out_ms: int | None,
    ) -> None:
        super().__init__()
        self._path = path
        self._key = key
        self._settings = settings
        self._marks = marks
        self._in_ms = in_ms
        self._out_ms = out_ms

    def run(self) -> None:
        import shutil

        dest = cache_folder(self._key)
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(self._path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        if fps < 1:
            fps = 30.0
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0, self._in_ms))
        index = 0
        estimated = 1
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if duration > 0:
            start_f = int(self._in_ms / 1000 * fps)
            end_f = int((self._out_ms or 10**9) / 1000 * fps)
            estimated = max(1, end_f - start_f)
        while not self.isInterruptionRequested():
            pos = int(cap.get(cv2.CAP_PROP_POS_MSEC) or 0)
            if self._out_ms is not None and pos >= self._out_ms:
                break
            ok, frame = cap.read()
            if not ok:
                break
            out, _, _ = protect_frame(
                frame,
                face_blur=self._settings.face_blur,
                text_blur=self._settings.text_blur,
                marks=self._marks,
                strength=self._settings.blur_strength,
            )
            fitted = fit_letterbox(out)
            cv2.imwrite(str(dest / f"{index:06d}.jpg"), fitted, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
            index += 1
            self.progress.emit(index, estimated)
        cap.release()
        if self.isInterruptionRequested() or index < 1:
            shutil.rmtree(dest, ignore_errors=True)
            return
        (dest / "meta.json").write_text(
            json.dumps({"count": index, "fps": fps, "in_ms": self._in_ms, "out_ms": self._out_ms}),
            encoding="utf-8",
        )
        self.finished_ok.emit(self._key)

