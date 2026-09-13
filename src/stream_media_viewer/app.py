"""2 窓起動。配信用はゲートが開けるまで隠す。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QDate, QThread, Signal
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from stream_media_viewer.detect.protect import protect_frame
from stream_media_viewer.i18n import t
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.scan import load_rgb_image, scan_folder
from stream_media_viewer.playback.video import VideoPlayer
from stream_media_viewer.render.canvas import fit_letterbox, rgb_to_bgr
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.settings import AppSettings, load_settings, save_settings
from stream_media_viewer.ui.operator_window import OperatorWindow
from stream_media_viewer.ui.output_window import OutputWindow
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap


class ProtectThread(QThread):
    done = Signal(object, bool, bool)

    def __init__(self, bgr: np.ndarray, settings: AppSettings, marks: list[dict]) -> None:
        super().__init__()
        self._bgr = bgr
        self._settings = settings
        self._marks = marks

    def run(self) -> None:
        out, faces, texts = protect_frame(
            self._bgr,
            face_blur=self._settings.face_blur,
            text_blur=self._settings.text_blur,
            marks=self._marks,
            strength=self._settings.blur_strength,
        )
        self.done.emit(out, faces, texts)


class StreamMediaViewerApp:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings if settings is not None else load_settings()
        self.gate = OutputGate()
        if self.settings.use_standby and self.settings.standby_path:
            self.gate.enable_standby(True)
        self.operator = OperatorWindow(self.gate)
        self.output = OutputWindow(self.gate)
        self.operator.lang = self.settings.language
        self.operator.retranslate()
        self._items: list[MediaItem] = []
        self._visible: list[int] = []
        self._index = 0
        self._preview: np.ndarray | None = None
        self._live: np.ndarray | None = None
        self._worker: ProtectThread | None = None
        self._undo: list[list[dict]] = []
        self._video = VideoPlayer()
        self._video.frame_ready.connect(self._on_video_frame)
        self._video.finished.connect(self._on_video_finished)
        self._playing_to_output = False
        self._live_path = ""
        self._wire()
        self._restore_checks()
        if self.settings.last_folder:
            self._load_folder(Path(self.settings.last_folder))
        self._sync_windows()

    def _wire(self) -> None:
        op = self.operator
        op.open_folder_requested.connect(self._pick_folder)
        op.send_requested.connect(self._on_send)
        op.panic_requested.connect(self._on_panic)
        op.prev_requested.connect(lambda: self._step(-1))
        op.next_requested.connect(lambda: self._step(1))
        op.play_requested.connect(self._toggle_play)
        op.star_requested.connect(self._toggle_star)
        op.undo_requested.connect(self._undo_mark)
        op.language_requested.connect(self._toggle_lang)
        op.item_selected.connect(self._select_visible)
        op.mark_added.connect(self._add_mark)
        op.settings_changed.connect(self._on_settings_ui)
        op.standby_requested.connect(self._pick_standby)
        op.timeline.sliderReleased.connect(self._apply_in_out)
        op.timeline_out.sliderReleased.connect(self._apply_in_out)

    def _restore_checks(self) -> None:
        op = self.operator
        op.chk_face.setChecked(self.settings.face_blur)
        op.chk_text.setChecked(self.settings.text_blur)
        op.chk_audio.setChecked(self.settings.video_audio)
        if self.settings.operator_geometry:
            self.operator.restoreGeometry(bytes.fromhex(self.settings.operator_geometry))

    def _on_settings_ui(self) -> None:
        prev_face = self.settings.face_blur
        self.settings.face_blur = self.operator.chk_face.isChecked()
        self.settings.text_blur = self.operator.chk_text.isChecked()
        self.settings.video_audio = self.operator.chk_audio.isChecked()
        if prev_face and not self.settings.face_blur:
            self.settings.blur_off_confirmed = False
        item = self._current()
        if item:
            self.settings.note_for(str(item.path)).loop = self.operator.chk_loop.isChecked()
        self._refresh_list()
        self._reload_current()

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self.operator, t(self.settings.language, "pick_folder"), self.settings.last_folder
        )
        if path:
            self.settings.last_folder = path
            self._load_folder(Path(path))

    def _pick_standby(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self.operator, t(self.settings.language, "standby"))
        if not path:
            self.settings.use_standby = False
            self.settings.standby_path = ""
            self.gate.enable_standby(False)
            self._sync_windows()
            return
        self.settings.standby_path = path
        self.settings.use_standby = True
        if self.gate.masked:
            self.gate.enable_standby(True)
            image = load_rgb_image(Path(path))
            if image is not None:
                frame = fit_letterbox(rgb_to_bgr(np.array(image)))
                self.output.show_frame(frame)
        self._sync_windows()

    def _load_folder(self, folder: Path) -> None:
        self._items = scan_folder(folder)
        self._index = 0
        self._refresh_list()
        if self._visible:
            self._select_visible(0)

    def _passes_filter(self, item: MediaItem) -> bool:
        op = self.operator
        note = self.settings.note_for(str(item.path))
        if op.chk_star_only.isChecked() and not note.favorite:
            return False
        if op.chk_photos.isChecked() and item.kind != "image":
            return False
        if op.chk_videos.isChecked() and item.kind != "video":
            return False
        if op.chk_faces.isChecked() and not item.has_face:
            return False
        if op.chk_gps.isChecked() and not item.has_gps:
            return False
        captured = item.captured_at
        if captured and op.chk_dates.isChecked():
            start = op.date_from.date()
            end = op.date_to.date()
            day = QDate(captured.year, captured.month, captured.day)
            if day < start or day > end:
                return False
        return True

    def _refresh_list(self) -> None:
        self._visible = [i for i, item in enumerate(self._items) if self._passes_filter(item)]
        labels = []
        for i in self._visible:
            item = self._items[i]
            note = self.settings.note_for(str(item.path))
            star = "⭐ " if note.favorite else ""
            warn = ""
            if item.has_face or (self.settings.text_blur and item.has_text_region):
                warn = "⚠ "
            when = item.captured_at.strftime("%Y-%m-%d %H:%M") if item.captured_at else ""
            place = t(self.settings.language, "place_yes") if item.has_gps else ""
            labels.append(f"{star}{warn}{item.path.name}\n{when} {place}".strip())
        self.operator.set_items([self._items[i] for i in self._visible], labels)

    def _current(self) -> MediaItem | None:
        if not self._visible:
            return None
        self._index = max(0, min(self._index, len(self._visible) - 1))
        return self._items[self._visible[self._index]]

    def _select_visible(self, row: int) -> None:
        if row < 0 or row >= len(self._visible):
            return
        self._index = row
        self._reload_current()

    def _step(self, delta: int) -> None:
        if not self._visible:
            return
        self._index = (self._index + delta) % len(self._visible)
        self.operator.list.setCurrentRow(self._index)

    def _reload_current(self) -> None:
        item = self._current()
        self._video.close()
        self._playing_to_output = False
        self.gate.begin_load()
        if item is None:
            self.operator.meta.setText(t(self.settings.language, "empty"))
            self.operator.refresh_status()
            return
        note = self.settings.note_for(str(item.path))
        self.operator.chk_loop.setChecked(note.loop)
        self.operator.btn_star.setChecked(note.favorite)
        when = item.captured_at.strftime("%Y-%m-%d %H:%M") if item.captured_at else ""
        place = t(self.settings.language, "place_yes") if item.has_gps else ""
        self.operator.meta.setText(f"{item.path.name}  {when}  {place}".strip())
        self.operator.meta.setToolTip(str(item.path))
        if item.kind == "image":
            image = load_rgb_image(item.path)
            if image is None:
                item.readable = False
                self.operator.meta.setText(t(self.settings.language, "unreadable"))
                self.operator.refresh_status()
                return
            bgr = rgb_to_bgr(np.array(image))
            self._start_protect(bgr, note.marks)
        else:
            fps = self._video.open(str(item.path))
            duration = self._video.duration_ms()
            self.operator.timeline.setRange(0, max(1, duration))
            self.operator.timeline_out.setRange(0, max(1, duration))
            self.operator.timeline.setValue(note.in_ms)
            self.operator.timeline_out.setValue(note.out_ms if note.out_ms else duration)
            self._video.in_ms = note.in_ms
            self._video.out_ms = note.out_ms
            self._video.loop = note.loop
            frame = self._video.seek_ms(note.in_ms)
            if frame is None:
                self.operator.meta.setText(t(self.settings.language, "unreadable"))
                return
            self._start_protect(frame, note.marks)
            _ = fps

    def _start_protect(self, bgr: np.ndarray, marks: list[dict]) -> None:
        prefix = self.operator.meta.text().split(" · ")[0]
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, 'processing')}")
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
        self._worker = ProtectThread(bgr, self.settings, list(marks))
        self._worker.done.connect(self._on_protected)
        self._worker.start()

    def _on_protected(self, bgr: np.ndarray, has_face: bool, has_text: bool) -> None:
        item = self._current()
        if item:
            item.has_face = has_face
            item.has_text_region = has_text
        fitted = fit_letterbox(bgr)
        self._preview = fitted
        self.operator.preview.set_frame(bgr_to_pixmap(fitted))
        self.gate.mark_processed()
        self.operator.refresh_status()

    def _on_send(self) -> None:
        if self._preview is None:
            return
        if not self.settings.face_blur and not self.settings.blur_off_confirmed:
            answer = QMessageBox.question(
                self.operator, "", t(self.settings.language, "confirm_no_blur")
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.settings.blur_off_confirmed = True
        if not self.gate.send_to_output():
            return
        self._live = self._preview
        item = self._current()
        if item:
            self._live_path = str(item.path)
        self.output.show_frame(self._live)
        item = self._current()
        if item and item.kind == "video":
            note = self.settings.note_for(str(item.path))
            self._video.loop = note.loop
            self._video.in_ms = note.in_ms
            self._video.out_ms = note.out_ms
            self._video.set_protect(lambda frame: self._protect_sync(frame, note.marks))
            self._playing_to_output = True
            self._video.seek_ms(note.in_ms)
            self._video.play()
        self._sync_windows()
        self.operator.refresh_status()

    def _protect_sync(self, frame: np.ndarray, marks: list[dict]) -> np.ndarray:
        out, _, _ = protect_frame(
            frame,
            face_blur=self.settings.face_blur,
            text_blur=self.settings.text_blur,
            marks=marks,
            strength=self.settings.blur_strength,
        )
        return fit_letterbox(out)

    def _on_video_frame(self, frame: np.ndarray) -> None:
        fitted = frame if frame.shape[0] == 1080 else fit_letterbox(frame)
        self.operator.preview.set_frame(bgr_to_pixmap(fitted))
        if self._playing_to_output and self.gate.window_visible:
            self._live = fitted
            self.output.show_frame(fitted)

    def _on_video_finished(self) -> None:
        self._playing_to_output = False

    def _toggle_play(self) -> None:
        item = self._current()
        if item is None or item.kind != "video":
            return
        note = self.settings.note_for(str(item.path))
        if self._video.playing:
            self._video.pause()
            return
        self._video.set_protect(lambda frame: self._protect_sync(frame, note.marks))
        item = self._current()
        self._playing_to_output = bool(
            item and self._live_path == str(item.path) and not self.gate.masked
        )
        self._video.seek_ms(note.in_ms)
        self._video.play()

    def _on_panic(self) -> None:
        self._video.pause()
        self._playing_to_output = False
        self._live_path = ""
        self.gate.panic()
        self._sync_windows()
        self.operator.refresh_status()

    def _toggle_star(self) -> None:
        item = self._current()
        if not item:
            return
        note = self.settings.note_for(str(item.path))
        note.favorite = not note.favorite
        self.operator.btn_star.setChecked(note.favorite)
        self._refresh_list()

    def _add_mark(self, mark: dict) -> None:
        item = self._current()
        if not item:
            return
        note = self.settings.note_for(str(item.path))
        self._undo.append(list(note.marks))
        self._undo = self._undo[-10:]
        note.marks.append(mark)
        self._reload_current()

    def _undo_mark(self) -> None:
        item = self._current()
        if not item or not self._undo:
            return
        self.settings.note_for(str(item.path)).marks = self._undo.pop()
        self._reload_current()

    def _apply_in_out(self) -> None:
        item = self._current()
        if not item or item.kind != "video":
            return
        note = self.settings.note_for(str(item.path))
        note.in_ms = min(self.operator.timeline.value(), self.operator.timeline_out.value())
        note.out_ms = max(self.operator.timeline.value(), self.operator.timeline_out.value())
        self._video.in_ms = note.in_ms
        self._video.out_ms = note.out_ms

    def _toggle_lang(self) -> None:
        self.settings.language = "en" if self.settings.language == "ja" else "ja"
        self.operator.lang = self.settings.language
        self.operator.retranslate()
        self._refresh_list()
        self._reload_current()

    def _sync_windows(self) -> None:
        self.output.refresh()
        self.operator.refresh_status()

    def show(self) -> None:
        self.operator.show()
        self._sync_windows()
        self.operator.raise_()
        self.operator.activateWindow()

    def persist(self) -> None:
        geo = self.operator.saveGeometry()
        self.settings.operator_geometry = geo.toHex().data().decode("ascii")
        save_settings(self.settings)


def run() -> int:
    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("StreamMediaViewer")
    app = StreamMediaViewerApp()
    qt_app.aboutToQuit.connect(app.persist)
    app.show()
    return qt_app.exec()
