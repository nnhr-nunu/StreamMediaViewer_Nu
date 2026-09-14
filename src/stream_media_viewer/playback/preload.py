from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
from PySide6.QtCore import QThread, Signal

from stream_media_viewer.config import SUPPORTED_VIDEO_SUFFIXES, user_config_dir
from stream_media_viewer.detect.faces import FaceHold
from stream_media_viewer.detect.protect import protect_for_note
from stream_media_viewer.errors import log_exception
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.render.canvas import fit_letterbox
from stream_media_viewer.render.enhance import enhance_bgr
from stream_media_viewer.settings import AppSettings, parse_face_pipeline


def preload_root() -> Path:
    root = user_config_dir() / "preload"
    root.mkdir(parents=True, exist_ok=True)
    return root


BYTES_PER_FRAME = 120_000


def format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.1f} GB"


def folder_cache_id(folder: Path | str) -> str:
    path = Path(folder)
    try:
        resolved = str(path.resolve())
    except OSError:
        resolved = str(path)
    return hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]


def item_cache_dir(folder_id: str, key: str) -> Path:
    return preload_root() / folder_id / key


def cache_size_bytes(folder_id: str | None = None) -> int:
    root = preload_root() if folder_id is None else preload_root() / folder_id
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total


def clear_folder_cache(folder_id: str) -> None:
    import shutil

    shutil.rmtree(preload_root() / folder_id, ignore_errors=True)


def clear_preload_cache() -> None:
    import shutil

    root = preload_root()
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)


def estimate_item_bytes(kind: str, duration_ms: int, fps: float = 30.0) -> int:
    if kind != "video":
        return BYTES_PER_FRAME
    seconds = max(1.0, duration_ms / 1000.0)
    rate = fps if fps > 1 else 30.0
    return int(seconds * rate * BYTES_PER_FRAME)


def cache_key(
    path: Path,
    *,
    in_ms: int,
    out_ms: int | None,
    face_blur: bool,
    text_blur: bool,
    strength: int,
    marks: list[dict[str, Any]],
    enhance_level: str = "off",
    skip_faces: bool = False,
    false_face_hashes: list[str] | None = None,
    rotation: int = 0,
    face_pipeline: str = "accurate",
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
        "enhance_level": enhance_level,
        "skip_faces": skip_faces,
        "false_face_hashes": list(false_face_hashes or []),
        "rotation": int(rotation or 0),
        "face_pipeline": parse_face_pipeline(face_pipeline),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def cache_folder(key: str, folder_id: str) -> Path:
    return item_cache_dir(folder_id, key)


def cache_is_ready(key: str, folder_id: str) -> bool:
    dest = item_cache_dir(folder_id, key)
    meta = dest / "meta.json"
    if not meta.is_file():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    count = int(data.get("count") or 0)
    if count < 1:
        return False
    last = dest / f"{count - 1:06d}.jpg"
    return last.is_file()


def read_meta(key: str, folder_id: str) -> dict[str, Any]:
    meta = item_cache_dir(folder_id, key) / "meta.json"
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
        folder_id: str,
    ) -> None:
        super().__init__()
        self._path = path
        self._key = key
        self._settings = settings
        self._marks = marks
        self._in_ms = in_ms
        self._out_ms = out_ms
        self._folder_id = folder_id
        self._face_hold = FaceHold()

    def _protect_frame(self, bgr: Any) -> tuple[Any, bool, bool]:
        note = self._settings.note_for(str(self._path))
        snap = FileNote(
            marks=self._marks,
            skip_faces=note.skip_faces,
            rotation=note.rotation,
        )
        return protect_for_note(bgr, self._settings, snap, face_hold=self._face_hold)

    def run(self) -> None:
        try:
            self._run()
        except Exception as exc:
            log_exception(exc)
            self.finished_ok.emit(self._key)

    def _run(self) -> None:
        import shutil

        dest = item_cache_dir(self._folder_id, self._key)
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)
        suffix = self._path.suffix.lower()
        if suffix not in SUPPORTED_VIDEO_SUFFIXES:
            self._run_image(dest)
            return
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
        saw_face = False
        saw_text = False
        while not self.isInterruptionRequested():
            pos = int(cap.get(cv2.CAP_PROP_POS_MSEC) or 0)
            if self._out_ms is not None and pos >= self._out_ms:
                break
            ok, frame = cap.read()
            if not ok:
                break
            out, faces, texts = self._protect_frame(frame)
            if out is None:
                continue
            saw_face = saw_face or faces
            saw_text = saw_text or texts
            fitted = fit_letterbox(
                enhance_bgr(out, level=self._settings.enhance_level)
            )
            cv2.imwrite(str(dest / f"{index:06d}.jpg"), fitted, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
            index += 1
            self.progress.emit(index, estimated)
        cap.release()
        if self.isInterruptionRequested() or index < 1:
            shutil.rmtree(dest, ignore_errors=True)
            if not self.isInterruptionRequested():
                self.finished_ok.emit(self._key)
            return
        (dest / "meta.json").write_text(
            json.dumps(
                {
                    "count": index,
                    "fps": fps,
                    "in_ms": self._in_ms,
                    "out_ms": self._out_ms,
                    "has_face": saw_face,
                    "has_text_region": saw_text,
                }
            ),
            encoding="utf-8",
        )
        self.finished_ok.emit(self._key)

    def _run_image(self, dest: Path) -> None:
        import shutil

        import numpy as np

        from stream_media_viewer.library.scan import load_rgb_image
        from stream_media_viewer.render.canvas import rgb_to_bgr

        image = load_rgb_image(self._path)
        if image is None:
            shutil.rmtree(dest, ignore_errors=True)
            self.finished_ok.emit(self._key)
            return
        bgr = rgb_to_bgr(np.array(image))
        out, faces, texts = self._protect_frame(bgr)
        if out is None:
            shutil.rmtree(dest, ignore_errors=True)
            self.finished_ok.emit(self._key)
            return
        fitted = fit_letterbox(enhance_bgr(out, level=self._settings.enhance_level))
        cv2.imwrite(str(dest / "000000.jpg"), fitted, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
        (dest / "meta.json").write_text(
            json.dumps(
                {
                    "count": 1,
                    "fps": 1,
                    "in_ms": 0,
                    "out_ms": None,
                    "has_face": faces,
                    "has_text_region": texts,
                }
            ),
            encoding="utf-8",
        )
        self.progress.emit(1, 1)
        self.finished_ok.emit(self._key)

