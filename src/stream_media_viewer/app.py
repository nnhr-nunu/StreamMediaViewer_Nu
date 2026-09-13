"""2 窓起動。配信用はゲートが開けるまで隠す。"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QDate, QThread, Signal
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QMessageBox

from stream_media_viewer.detect.protect import protect_frame
from stream_media_viewer.i18n import t
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.scan import load_rgb_image, scan_folder
from stream_media_viewer.playback.preload import (
    PreloadWorker,
    cache_folder,
    cache_is_ready,
    cache_key,
    cache_size_bytes,
    clear_folder_cache,
    clear_preload_cache,
    estimate_item_bytes,
    folder_cache_id,
    format_bytes,
    read_meta,
)
from stream_media_viewer.playback.video import VideoPlayer
from stream_media_viewer.render.canvas import fit_letterbox, rgb_to_bgr
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.settings import AppSettings, load_settings, remember_folder, save_settings
from stream_media_viewer.ui.geometry import geometry_hex, restore_saved_geometry
from stream_media_viewer.ui.list_row import row_marks
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
        self._preload: PreloadWorker | None = None
        self._folder_queue: list[MediaItem] = []
        self._folder_total = 0
        self._wire()
        self._restore_checks()
        if self.settings.last_folder:
            self._open_folder_path(self.settings.last_folder)
        self._sync_windows()
        self._refresh_cache_label()

    def _wire(self) -> None:
        op = self.operator
        op.open_folder_requested.connect(self._on_folder_button)
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
        op.prepare_requested.connect(self._start_preload)
        op.prepare_folder_requested.connect(self._prepare_folder)
        op.clear_cache_requested.connect(self._clear_cache)
        op.timeline.sliderReleased.connect(self._apply_in_out)
        op.timeline_out.sliderReleased.connect(self._apply_in_out)

    def _restore_checks(self) -> None:
        op = self.operator
        op.chk_face.setChecked(self.settings.face_blur)
        op.chk_text.setChecked(self.settings.text_blur)
        op.chk_audio.setChecked(self.settings.video_audio)
        if self.settings.operator_geometry:
            self.operator.restoreGeometry(bytes.fromhex(self.settings.operator_geometry))
        restore_saved_geometry(self.output, self.settings.output_pos)

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

    def _on_folder_button(self) -> None:
        lang = self.settings.language
        recents = [path for path in self.settings.recent_folders if Path(path).is_dir()]
        if not recents:
            self._browse_folder()
            return
        menu = QMenu(self.operator)
        for path in recents:
            action = menu.addAction(Path(path).name or path)
            action.setToolTip(path)
            action.setData(path)
        menu.addSeparator()
        browse = menu.addAction(t(lang, "browse_folder"))
        chosen = menu.exec(self.operator.btn_folder.mapToGlobal(self.operator.btn_folder.rect().bottomLeft()))
        if chosen is None:
            return
        if chosen is browse:
            self._browse_folder()
            return
        path = str(chosen.data() or "")
        if path:
            self._open_folder_path(path)

    def _browse_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self.operator, t(self.settings.language, "pick_folder"), self.settings.last_folder
        )
        if path:
            self._open_folder_path(path)

    def _open_folder_path(self, path: str) -> None:
        self.settings.last_folder = path
        self.settings.recent_folders = remember_folder(self.settings.recent_folders, path)
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
        row = self.operator.list.currentRow()
        self._visible = [i for i, item in enumerate(self._items) if self._passes_filter(item)]
        labels = []
        for i in self._visible:
            item = self._items[i]
            note = self.settings.note_for(str(item.path))
            marks = row_marks(
                favorite=note.favorite,
                live=self._live_path == str(item.path) and not self.gate.masked,
                ready=cache_is_ready(self._key_for(item), self._folder_id()),
            )
            mark = f"{marks} " if marks else ""
            warn = ""
            if item.has_face or (self.settings.text_blur and item.has_text_region):
                warn = "⚠ "
            when = item.captured_at.strftime("%Y-%m-%d %H:%M") if item.captured_at else ""
            place = t(self.settings.language, "place_yes") if item.has_gps else ""
            labels.append(f"{mark}{warn}{item.path.name}\n{when} {place}".strip())
        self.operator.set_items([self._items[i] for i in self._visible], labels)
        if 0 <= row < self.operator.list.count():
            self.operator.list.blockSignals(True)
            self.operator.list.setCurrentRow(row)
            self.operator.list.blockSignals(False)

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
        if not self._folder_queue:
            self._stop_preload()
        item = self._current()
        self._video.close()
        self._playing_to_output = False
        self.gate.begin_load()
        if item is None:
            self.operator.set_range_visible(False)
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
        self.operator.set_range_visible(item.kind == "video")
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
        item = self._current()
        if item and item.kind == "video" and not self._folder_queue:
            self._start_preload()

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
            self._video.audio_enabled = self.settings.video_audio
            self._playing_to_output = True
            self._bind_cache(item)
            self._video.seek_ms(note.in_ms)
            self._video.play()
        self._sync_windows()
        self.operator.refresh_status()
        self._refresh_list()

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
        self._video.audio_enabled = self._playing_to_output and self.settings.video_audio
        if item:
            self._bind_cache(item)
        self._video.seek_ms(note.in_ms)
        self._video.play()

    def _on_panic(self) -> None:
        self._video.pause()
        self._playing_to_output = False
        self._live_path = ""
        self.gate.panic()
        self._sync_windows()
        self.operator.refresh_status()
        self._refresh_list()

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
        if not self._folder_queue:
            self._stop_preload()
            self._start_preload()

    def _key_for(self, item: MediaItem) -> str:
        note = self.settings.note_for(str(item.path))
        return cache_key(
            item.path,
            in_ms=note.in_ms,
            out_ms=note.out_ms,
            face_blur=self.settings.face_blur,
            text_blur=self.settings.text_blur,
            strength=self.settings.blur_strength,
            marks=note.marks,
        )

    def _folder_id(self) -> str:
        folder = self.settings.last_folder or "_none"
        return folder_cache_id(folder)

    def _bind_cache(self, item: MediaItem) -> None:
        key = self._key_for(item)
        folder_id = self._folder_id()
        if cache_is_ready(key, folder_id):
            meta = read_meta(key, folder_id)
            self._video.set_cache(cache_folder(key, folder_id), float(meta.get("fps") or 30))
            return
        self._video.set_cache(None, 30)

    def _stop_preload(self) -> None:
        if self._preload is not None and self._preload.isRunning():
            self._preload.requestInterruption()
            self._preload.wait(1500)
        self._preload = None

    def _start_preload(self) -> None:
        if self._folder_queue:
            return
        item = self._current()
        if item is None:
            return
        self._start_preload_for(item)

    def _start_preload_for(self, item: MediaItem) -> None:
        note = self.settings.note_for(str(item.path))
        key = self._key_for(item)
        lang = self.settings.language
        prefix = self.operator.meta.text().split(" · ")[0]
        if cache_is_ready(key, self._folder_id()):
            self.operator.meta.setText(f"{prefix} · {t(lang, 'prepared')}")
            if self._folder_queue:
                self._advance_folder_queue()
            return
        if self._preload is not None and self._preload.isRunning():
            return
        self._preload = PreloadWorker(
            item.path,
            key,
            self.settings,
            list(note.marks),
            note.in_ms,
            note.out_ms,
            self._folder_id(),
        )
        self._preload.progress.connect(self._on_preload_progress)
        self._preload.finished_ok.connect(self._on_preload_done)
        self._preload.start()

    def _on_preload_progress(self, done: int, total: int) -> None:
        prefix = self.operator.meta.text().split(" · ")[0]
        if self._folder_queue:
            finished = self._folder_total - len(self._folder_queue)
            folder = t(self.settings.language, "folder_progress").format(
                done=finished + 1, total=max(1, self._folder_total)
            )
            self.operator.meta.setText(f"{prefix} · {folder} ({done}/{max(1, total)})")
            return
        label = t(self.settings.language, "preparing")
        self.operator.meta.setText(f"{prefix} · {label} {done}/{max(1, total)}")

    def _on_preload_done(self, _key: str) -> None:
        prefix = self.operator.meta.text().split(" · ")[0]
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, 'prepared')}")
        self._refresh_cache_label()
        self._refresh_list()
        self._advance_folder_queue()

    def _advance_folder_queue(self) -> None:
        if not self._folder_queue:
            self._refresh_cache_label()
            self._refresh_list()
            return
        self._folder_queue.pop(0)
        if not self._folder_queue:
            self._refresh_cache_label()
            self._refresh_list()
            return
        self._start_preload_for(self._folder_queue[0])

    def _prepare_folder(self) -> None:
        if not self._items:
            return
        lang = self.settings.language
        pending: list[MediaItem] = []
        total_bytes = 0
        for item in self._items:
            if cache_is_ready(self._key_for(item), self._folder_id()):
                continue
            pending.append(item)
            note = self.settings.note_for(str(item.path))
            duration_ms = 0
            fps = 30.0
            if item.kind == "video":
                cap = cv2.VideoCapture(str(item.path))
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
                frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                cap.release()
                full_ms = int(1000 * frames / max(fps, 1.0)) if frames else 0
                end = note.out_ms if note.out_ms else full_ms
                duration_ms = max(0, end - note.in_ms)
            total_bytes += estimate_item_bytes(item.kind, duration_ms, fps)
        if not pending:
            QMessageBox.information(
                self.operator, "", t(lang, "prepared")
            )
            self._refresh_cache_label()
            return
        ask = t(lang, "prepare_folder_ask").format(size=format_bytes(total_bytes))
        if QMessageBox.question(self.operator, "", ask) != QMessageBox.StandardButton.Yes:
            return
        self._stop_preload()
        self._folder_queue = pending
        self._folder_total = len(pending)
        self._start_preload_for(pending[0])

    def _clear_cache(self) -> None:
        lang = self.settings.language
        folder_size = format_bytes(cache_size_bytes(self._folder_id()))
        total_size = format_bytes(cache_size_bytes())
        ask = t(lang, "clear_cache_ask").format(folder=folder_size, total=total_size)
        box = QMessageBox(self.operator)
        box.setText(ask)
        this_btn = box.addButton(t(lang, "clear_this_folder"), QMessageBox.ButtonRole.AcceptRole)
        all_btn = box.addButton(t(lang, "clear_all_cache"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(t(lang, "cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is not this_btn and clicked is not all_btn:
            return
        self._stop_preload()
        self._folder_queue = []
        if clicked is this_btn:
            clear_folder_cache(self._folder_id())
        else:
            clear_preload_cache()
        self._video.set_cache(None, 30)
        self._refresh_cache_label()
        self._refresh_list()

    def _refresh_cache_label(self) -> None:
        folder = format_bytes(cache_size_bytes(self._folder_id()))
        total = format_bytes(cache_size_bytes())
        self.operator.cache_label.setText(
            t(self.settings.language, "cache_label").format(folder=folder, total=total)
        )

    def _toggle_lang(self) -> None:
        self.settings.language = "en" if self.settings.language == "ja" else "ja"
        self.operator.lang = self.settings.language
        self.operator.retranslate()
        self._refresh_cache_label()
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
        self.settings.output_pos = geometry_hex(self.output)
        save_settings(self.settings)


def run() -> int:
    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("StreamMediaViewer")
    app = StreamMediaViewerApp()
    qt_app.aboutToQuit.connect(app.persist)
    app.show()
    return qt_app.exec()
