"""2 窓起動。配信用はゲートが開けるまで隠す。"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QDate, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMenu, QMessageBox

from stream_media_viewer.detect.protect import protect_frame_safe
from stream_media_viewer.errors import install_excepthook, log_exception
from stream_media_viewer.i18n import t
from stream_media_viewer.library.filters import passes_filters
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.protect_cache import ProtectFrameCache
from stream_media_viewer.library.scan import load_rgb_image
from stream_media_viewer.library.workers import ScanWorker, ThumbWorker
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
from stream_media_viewer.render.enhance import enhance_bgr, next_enhance_level
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.settings import AppSettings, load_settings, remember_folder, save_settings
from stream_media_viewer.ui.geometry import geometry_hex, restore_saved_geometry
from stream_media_viewer.ui.list_row import row_marks
from stream_media_viewer.ui.operator_window import OperatorWindow
from stream_media_viewer.ui.output_window import OutputWindow
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap
from stream_media_viewer.ui.settings_dialog import SettingsDialog, SettingsDraft


class ProtectThread(QThread):
    done = Signal(object, bool, bool, int)
    failed = Signal(int)

    def __init__(
        self, bgr: np.ndarray, settings: AppSettings, marks: list[dict], seq: int
    ) -> None:
        super().__init__()
        self._bgr = bgr
        self._settings = settings
        self._marks = marks
        self.seq = seq

    def run(self) -> None:
        try:
            out, faces, texts = protect_frame_safe(
                self._bgr,
                face_blur=self._settings.face_blur,
                text_blur=self._settings.text_blur,
                marks=self._marks,
                strength=self._settings.blur_strength,
            )
            if out is None:
                self.failed.emit(self.seq)
                return
            out = enhance_bgr(out, level=self._settings.enhance_level)
            self.done.emit(out, faces, texts, self.seq)
        except Exception as exc:
            log_exception(exc)
            self.failed.emit(self.seq)


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
        self._protect_cache = ProtectFrameCache()
        self._thumb_pix: dict[str, QPixmap] = {}
        self._scan_worker: ScanWorker | None = None
        self._thumb_worker: ThumbWorker | None = None
        self._scan_token = 0
        self._protect_seq = 0
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
        else:
            self.operator.show_guide(t(self.settings.language, "empty_guide"))
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
        op.item_selected.connect(self._select_visible)
        op.mark_added.connect(self._add_mark)
        op.settings_changed.connect(self._on_settings_ui)
        op.filters_changed.connect(self._on_filters_ui)
        op.loop_changed.connect(self._on_loop_ui)
        op.standby_requested.connect(self._pick_standby)
        op.prepare_requested.connect(self._start_preload)
        op.prepare_folder_requested.connect(self._prepare_folder)
        op.clear_cache_requested.connect(self._clear_cache)
        op.enhance_cycle_requested.connect(self._cycle_enhance)
        op.settings_requested.connect(self._open_settings)
        op.timeline.sliderReleased.connect(self._apply_in_out)
        op.timeline_out.sliderReleased.connect(self._apply_in_out)
        op.destroyed.connect(self._on_operator_gone)

    def _restore_checks(self) -> None:
        op = self.operator
        op.chk_face.setChecked(self.settings.face_blur)
        op.chk_text.setChecked(self.settings.text_blur)
        self.operator.set_enhance_level(self.settings.enhance_level)
        op.date_from.blockSignals(True)
        op.date_to.blockSignals(True)
        if self.settings.date_from:
            parsed = QDate.fromString(self.settings.date_from, "yyyy-MM-dd")
            if parsed.isValid():
                op.date_from.setDate(parsed)
        if self.settings.date_to:
            parsed = QDate.fromString(self.settings.date_to, "yyyy-MM-dd")
            if parsed.isValid():
                op.date_to.setDate(parsed)
        op.date_from.blockSignals(False)
        op.date_to.blockSignals(False)
        if self.settings.operator_geometry:
            self.operator.restoreGeometry(bytes.fromhex(self.settings.operator_geometry))
        restore_saved_geometry(self.output, self.settings.output_pos)

    def _on_settings_ui(self) -> None:
        prev_face = self.settings.face_blur
        self.settings.face_blur = self.operator.chk_face.isChecked()
        self.settings.text_blur = self.operator.chk_text.isChecked()
        self.settings.enhance_level = self.operator.enhance_level
        if prev_face and not self.settings.face_blur:
            self.settings.blur_off_confirmed = False
        self._protect_cache.clear()
        self._reload_current()

    def _on_filters_ui(self) -> None:
        self.settings.date_from = self.operator.date_from.date().toString("yyyy-MM-dd")
        self.settings.date_to = self.operator.date_to.date().toString("yyyy-MM-dd")
        self._refresh_list()

    def _on_loop_ui(self) -> None:
        item = self._current()
        if item:
            self.settings.note_for(str(item.path)).loop = self.operator.chk_loop.isChecked()

    def _cycle_enhance(self) -> None:
        self.settings.enhance_level = next_enhance_level(self.settings.enhance_level)
        self.operator.set_enhance_level(self.settings.enhance_level)
        self._protect_cache.clear()
        self._reload_current()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            self.operator,
            SettingsDraft(
                blur_strength=self.settings.blur_strength,
                face_blur=self.settings.face_blur,
                text_blur=self.settings.text_blur,
                video_audio=self.settings.video_audio,
                enhance_level=self.settings.enhance_level,
                language=self.settings.language,
                include_subfolders=self.settings.include_subfolders,
            ),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        applied = dialog.draft()
        prev_face = self.settings.face_blur
        prev_sub = self.settings.include_subfolders
        self.settings.blur_strength = applied.blur_strength
        self.settings.face_blur = applied.face_blur
        self.settings.text_blur = applied.text_blur
        self.settings.video_audio = applied.video_audio
        self.settings.enhance_level = applied.enhance_level
        self.settings.language = applied.language
        self.settings.include_subfolders = applied.include_subfolders
        if prev_face and not self.settings.face_blur:
            self.settings.blur_off_confirmed = False
        op = self.operator
        op.chk_face.blockSignals(True)
        op.chk_text.blockSignals(True)
        op.chk_face.setChecked(applied.face_blur)
        op.chk_text.setChecked(applied.text_blur)
        op.chk_face.blockSignals(False)
        op.chk_text.blockSignals(False)
        op.lang = applied.language
        op.set_enhance_level(applied.enhance_level)
        op.retranslate()
        self._protect_cache.clear()
        if prev_sub != applied.include_subfolders and self.settings.last_folder:
            self._open_folder_path(self.settings.last_folder)
            return
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
        anchor = self.operator.btn_folder.rect().bottomLeft()
        chosen = menu.exec(self.operator.btn_folder.mapToGlobal(anchor))
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
        self._start_scan(Path(path))

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

    def _start_scan(self, folder: Path) -> None:
        self._scan_token += 1
        token = self._scan_token
        if self._thumb_worker is not None and self._thumb_worker.isRunning():
            self._thumb_worker.requestInterruption()
        self._thumb_worker = None
        self._thumb_pix.clear()
        self._protect_cache.clear()
        self._items = []
        self._visible = []
        self._index = 0
        self.operator.set_items([], [])
        self.operator.set_media_kind(None)
        self.operator.show_guide(t(self.settings.language, "scanning"))
        self.operator.meta.setText(t(self.settings.language, "scanning").split("\n")[0])
        worker = ScanWorker(folder, recursive=self.settings.include_subfolders)
        worker.finished_items.connect(lambda items, tok=token: self._on_scan_done(items, tok))
        worker.start()
        self._scan_worker = worker

    def _on_scan_done(self, items: object, token: int) -> None:
        if token != self._scan_token:
            return
        self._items = list(items) if isinstance(items, list) else []
        self._apply_saved_marks()
        self._index = 0
        self._refresh_list()
        if self._visible:
            self.operator.reveal_preview()
            self._select_visible(0)
        else:
            self.operator.set_media_kind(None)
            self.operator.show_guide(t(self.settings.language, "folder_empty"))
            self.operator.meta.setText(t(self.settings.language, "folder_empty"))
            self.operator.refresh_status()
        self._start_thumbs()

    def _start_thumbs(self) -> None:
        if self._thumb_worker is not None and self._thumb_worker.isRunning():
            self._thumb_worker.requestInterruption()
        images = [item.path for item in self._items if item.kind == "image"]
        videos = [item.path for item in self._items if item.kind == "video"]
        if not images and not videos:
            self._thumb_worker = None
            return
        worker = ThumbWorker(images + videos)
        worker.thumb_ready.connect(self._on_thumb_ready)
        worker.start()
        self._thumb_worker = worker

    def _on_thumb_ready(self, src: str, dest: str) -> None:
        list_widget = getattr(self.operator, "list", None)
        try:
            alive = list_widget is not None and list_widget.count() >= 0
        except RuntimeError:
            return
        if not alive:
            return
        pix = QPixmap(dest)
        if pix.isNull():
            return
        self._thumb_pix[src] = pix
        for row, index in enumerate(self._visible):
            if str(self._items[index].path) == src:
                self.operator.set_row_icon(row, pix)
                break

    def _on_operator_gone(self, *_args: object) -> None:
        if self._thumb_worker is None:
            return
        try:
            self._thumb_worker.thumb_ready.disconnect(self._on_thumb_ready)
        except (TypeError, RuntimeError):
            pass
        if self._thumb_worker.isRunning():
            self._thumb_worker.requestInterruption()

    def _apply_saved_marks(self) -> None:
        for item in self._items:
            note = self.settings.note_for(str(item.path))
            item.has_face = note.has_face
            item.has_text_region = note.has_text_region

    def _passes_filter(self, item: MediaItem) -> bool:
        op = self.operator
        note = self.settings.note_for(str(item.path))
        return passes_filters(
            readable=item.readable,
            kind=item.kind,
            favorite=note.favorite,
            has_face=item.has_face,
            has_gps=item.has_gps,
            place_name=item.place_name,
            captured_at=item.captured_at,
            star_only=op.chk_star_only.isChecked(),
            photos=op.chk_photos.isChecked(),
            videos=op.chk_videos.isChecked(),
            faces=op.chk_faces.isChecked(),
            gps_yes=op.chk_gps.isChecked(),
            gps_no=op.chk_no_gps.isChecked(),
            place=op.selected_place(),
            dates=op.chk_dates.isChecked(),
            date_from=op.date_from.date().toPython(),
            date_to=op.date_to.date().toPython(),
            folder=op.selected_folder(),
            relative_folder=item.relative_folder,
        )

    def _refresh_list(self) -> None:
        current_path = ""
        if self._visible:
            current = self._current()
            if current is not None:
                current_path = str(current.path)
        selected_place = self.operator.selected_place()
        selected_folder = self.operator.selected_folder()
        places = sorted({item.place_name for item in self._items if item.place_name})
        folders = sorted({item.relative_folder for item in self._items if item.relative_folder})
        self.operator.set_places(places, selected_place)
        self.operator.set_folders(folders, selected_folder)
        self._visible = [i for i, item in enumerate(self._items) if self._passes_filter(item)]
        labels: list[str] = []
        icons: list[QPixmap | None] = []
        tips: list[str] = []
        visible_items: list[MediaItem] = []
        for i in self._visible:
            item = self._items[i]
            visible_items.append(item)
            labels.append(self._row_label(item))
            icons.append(self._thumb_pix.get(str(item.path)))
            tips.append(self._row_tooltip(item))
        self.operator.set_items(visible_items, labels, icons, tips)
        row = 0
        if current_path:
            for index, item_index in enumerate(self._visible):
                if str(self._items[item_index].path) == current_path:
                    row = index
                    break
        if self._visible:
            self._index = row
            self.operator.list.blockSignals(True)
            self.operator.list.setCurrentRow(row)
            self.operator.list.blockSignals(False)

    def _row_label(self, item: MediaItem) -> str:
        note = self.settings.note_for(str(item.path))
        marks = row_marks(
            favorite=note.favorite,
            live=self._live_path == str(item.path) and not self.gate.masked,
            ready=cache_is_ready(self._key_for(item), self._folder_id()),
        )
        warn = "⚠" if item.has_face or (self.settings.text_blur and item.has_text_region) else ""
        when = item.captured_at.strftime("%m/%d") if item.captured_at else ""
        place = item.place_name
        lines = [part for part in (f"{marks} {warn}".strip(), when, place) if part]
        return "\n".join(lines)

    def _row_tooltip(self, item: MediaItem) -> str:
        when = item.captured_at.strftime("%Y-%m-%d %H:%M") if item.captured_at else ""
        place = item.place_name
        folder = item.relative_folder
        parts = [item.path.name]
        if folder:
            parts.append(folder)
        if when:
            parts.append(when)
        if place:
            parts.append(place)
        parts.append(str(item.path))
        return "\n".join(parts)

    def _sync_live_marks(self) -> None:
        for row, index in enumerate(self._visible):
            list_item = self.operator.list.item(row)
            if list_item is None:
                continue
            item = self._items[index]
            list_item.setText(self._row_label(item))
            list_item.setToolTip(self._row_tooltip(item))

    def _relabel_current_row(self) -> None:
        item = self._current()
        if item is None:
            return
        list_item = self.operator.list.item(self._index)
        if list_item is not None:
            list_item.setText(self._row_label(item))

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
            self.operator.set_media_kind(None)
            key = "folder_empty" if self.settings.last_folder else "empty_guide"
            self.operator.show_guide(t(self.settings.language, key))
            self.operator.meta.setText(t(self.settings.language, "empty"))
            self.operator.refresh_status()
            return
        self.operator.reveal_preview()
        note = self.settings.note_for(str(item.path))
        self.operator.chk_loop.blockSignals(True)
        self.operator.chk_loop.setChecked(note.loop)
        self.operator.chk_loop.blockSignals(False)
        self.operator.btn_star.setChecked(note.favorite)
        when = item.captured_at.strftime("%Y-%m-%d %H:%M") if item.captured_at else ""
        place = item.place_name
        self.operator.meta.setText(f"{when}  {place}".strip() or item.path.name)
        self.operator.meta.setToolTip(str(item.path))
        self.operator.set_media_kind(item.kind)
        if item.kind == "image":
            image = load_rgb_image(item.path)
            if image is None:
                self._mark_unreadable(item)
                return
            bgr = rgb_to_bgr(np.array(image))
            self._show_operator_frame(bgr)
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
                self._mark_unreadable(item)
                return
            self._show_operator_frame(frame)
            self._start_protect(frame, note.marks)
            _ = fps

    def _show_operator_frame(self, bgr: np.ndarray) -> None:
        self.operator.preview.set_frame(bgr_to_pixmap(fit_letterbox(bgr)), smooth=False)

    def _mark_unreadable(self, item: MediaItem) -> None:
        item.readable = False
        self._preview = None
        self.operator.set_media_kind(None)
        self.operator.meta.setText(t(self.settings.language, "unreadable"))
        self._refresh_list()
        self.operator.list.blockSignals(True)
        self.operator.list.setCurrentRow(-1)
        self.operator.list.blockSignals(False)
        self.operator.refresh_status()

    def _start_protect(self, bgr: np.ndarray, marks: list[dict]) -> None:
        self._protect_seq += 1
        seq = self._protect_seq
        item = self._current()
        if item is not None:
            cached = self._protect_cache.get(self._key_for(item))
            if cached is not None:
                self._on_protected(*cached, seq)
                return
        prefix = self.operator.meta.text().split(" · ")[0]
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, 'processing')}")
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
        self._worker = ProtectThread(bgr, self.settings, list(marks), seq)
        self._worker.done.connect(self._on_protected)
        self._worker.failed.connect(self._on_protect_failed)
        self._worker.start()

    def _on_protect_failed(self, seq: int) -> None:
        if seq != self._protect_seq:
            return
        self._preview = None
        self.operator.meta.setText(t(self.settings.language, "protect_failed"))
        self.operator.refresh_status()

    def _on_protected(self, bgr: np.ndarray, has_face: bool, has_text: bool, seq: int) -> None:
        if seq != self._protect_seq:
            return
        item = self._current()
        if item:
            item.has_face = has_face
            item.has_text_region = has_text
            note = self.settings.note_for(str(item.path))
            note.has_face = has_face
            note.has_text_region = has_text
            self._protect_cache.put(self._key_for(item), bgr, has_face, has_text)
        fitted = fit_letterbox(bgr)
        self._preview = fitted
        self.operator.reveal_preview()
        self.operator.preview.set_frame(bgr_to_pixmap(fitted))
        self.gate.mark_processed()
        self.operator.refresh_status()
        if self.operator.chk_faces.isChecked():
            self._refresh_list()
        else:
            self._relabel_current_row()
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
            cached = cache_is_ready(self._key_for(item), self._folder_id())
            if not cached and abs(self._video.position_ms() - note.in_ms) > 120:
                self._video.seek_ms(note.in_ms)
            self._video.play()
        self._sync_windows()
        self.operator.refresh_status()
        self._sync_live_marks()

    def _protect_sync(self, frame: np.ndarray, marks: list[dict]) -> np.ndarray:
        out, _, _ = protect_frame_safe(
            frame,
            face_blur=self.settings.face_blur,
            text_blur=self.settings.text_blur,
            marks=marks,
            strength=self.settings.blur_strength,
        )
        if out is None:
            raise RuntimeError("protect failed")
        out = enhance_bgr(out, level=self.settings.enhance_level)
        return fit_letterbox(out)

    def _on_video_frame(self, frame: np.ndarray) -> None:
        fitted = frame if frame.shape[0] == 1080 else fit_letterbox(frame)
        self.operator.preview.set_frame(bgr_to_pixmap(fitted), smooth=False)
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
        self._sync_live_marks()

    def _toggle_star(self) -> None:
        item = self._current()
        if not item:
            return
        note = self.settings.note_for(str(item.path))
        note.favorite = not note.favorite
        self.operator.btn_star.setChecked(note.favorite)
        if self.operator.chk_star_only.isChecked():
            self._refresh_list()
        else:
            self._relabel_current_row()

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
            enhance_level=self.settings.enhance_level,
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

    def _on_preload_done(self, key: str) -> None:
        folder_id = self._folder_id()
        if cache_is_ready(key, folder_id):
            try:
                meta = read_meta(key, folder_id)
            except (OSError, ValueError):
                meta = {}
            has_face = bool(meta.get("has_face"))
            has_text = bool(meta.get("has_text_region"))
            for item in self._items:
                if self._key_for(item) != key:
                    continue
                item.has_face = item.has_face or has_face
                item.has_text_region = item.has_text_region or has_text
                note = self.settings.note_for(str(item.path))
                note.has_face = item.has_face
                note.has_text_region = item.has_text_region
                break
        prefix = self.operator.meta.text().split(" · ")[0]
        label_key = "prepared" if cache_is_ready(key, folder_id) else "protect_failed"
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, label_key)}")
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
                try:
                    cap = cv2.VideoCapture(str(item.path))
                    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
                    frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                    cap.release()
                except Exception as exc:
                    log_exception(exc)
                    fps = 30.0
                    frames = 0.0
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

    def _sync_windows(self) -> None:
        self.output.refresh()
        self.operator.refresh_status()

    def show(self) -> None:
        self.operator.show()
        self._sync_windows()
        self.operator.raise_()
        self.operator.activateWindow()

    def persist(self) -> None:
        self._on_operator_gone()
        geo = self.operator.saveGeometry()
        self.settings.operator_geometry = geo.toHex().data().decode("ascii")
        self.settings.output_pos = geometry_hex(self.output)
        try:
            save_settings(self.settings)
        except OSError as exc:
            log_exception(exc)


def run() -> int:
    install_excepthook()
    try:
        qt_app = QApplication.instance() or QApplication(sys.argv)
        qt_app.setApplicationName("StreamMediaViewer")
        app = StreamMediaViewerApp()
        qt_app.aboutToQuit.connect(app.persist)
        app.show()
        return qt_app.exec()
    except Exception as exc:
        log_exception(exc)
        qt_app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "StreamMediaViewer(ぬ)", t("ja", "startup_failed"))
        return 1
