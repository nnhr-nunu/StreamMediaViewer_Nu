"""フォルダ走査と縮小画は裏で進める。操作画面を止めない。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from stream_media_viewer.errors import log_exception
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.scan import scan_folder
from stream_media_viewer.library.thumbs import ensure_thumb


class ScanWorker(QThread):
    finished_items = Signal(object)
    progress = Signal(str)

    def __init__(self, folder: Path, *, recursive: bool) -> None:
        super().__init__()
        self._folder = folder
        self._recursive = recursive

    def run(self) -> None:
        try:
            items = scan_folder(self._folder, recursive=self._recursive)
            self.finished_items.emit(items)
        except Exception as exc:
            log_exception(exc)
            self.finished_items.emit([])


class ThumbWorker(QThread):
    thumb_ready = Signal(str, str)

    def __init__(self, paths: list[Path]) -> None:
        super().__init__()
        self._paths = paths

    def run(self) -> None:
        for path in self._paths:
            if self.isInterruptionRequested():
                return
            try:
                dest = ensure_thumb(path)
            except Exception as exc:
                log_exception(exc)
                continue
            if dest is not None:
                self.thumb_ready.emit(str(path), str(dest))
