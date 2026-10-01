"""2 窓起動。配信用はゲートが開けるまで隠す。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QDate, QThread, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMenu, QMessageBox

from stream_media_viewer.detect.faces import (
    FaceHold,
    detect_face_boxes,
    face_box_at,
    remember_false_faces,
)
from stream_media_viewer.detect.false_faces import (
    load_shipped_hashes,
    try_remove_shipped_hash,
    try_update_shipped_catalog,
)
from stream_media_viewer.detect.protect import (
    PROTECT_LOCK,
    ProtectSettings,
    protect_for_note,
    protect_frame_safe,
)
from stream_media_viewer.errors import install_excepthook, log_exception, user_error_key
from stream_media_viewer.i18n import t
from stream_media_viewer.library.filters import passes_filters
from stream_media_viewer.library.auto_prep import PAUSE_POLL_MS, AutoPrepQueue
from stream_media_viewer.library.item import FileNote, MediaItem
from stream_media_viewer.library.neighbors import neighbor_rows
from stream_media_viewer.library.preview_load import ImageLoadWorker, PrefetchWorker
from stream_media_viewer.library.protect_cache import ProtectFrameCache
from stream_media_viewer.library.scan import load_rgb_image, merge_media_items
from stream_media_viewer.library.sort import sorted_items
from stream_media_viewer.library.thumbs import thumb_paths_for
from stream_media_viewer.library.workers import ScanWorker, ThumbWorker
from stream_media_viewer.playback.preload import (
    PreloadWorker,
    cache_is_ready,
    read_protected_image,
    write_protected_image,
)
from stream_media_viewer.playback.video import VideoPlayer
from stream_media_viewer.prep_flow import PrepFlowMixin
from stream_media_viewer.prep_flow import qthread_live as _qthread_live
from stream_media_viewer.render.canvas import fit_letterbox, rgb_to_bgr
from stream_media_viewer.render.enhance import enhance_bgr, next_enhance_level
from stream_media_viewer.render.rotate import clamp_rotation, rotate_bgr, rotate_marks
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.settings import (
    AppSettings,
    clamp_blur_strength,
    clamp_brush_width,
    load_settings,
    load_settings_with_error,
    remember_folder,
    save_settings,
)
from stream_media_viewer.ui.app_icon import apply_app_icon, configure_process_identity
from stream_media_viewer.ui.capture_exclude import (
    configure_dev_allow_capture,
    guard_popups_from_capture,
)
from stream_media_viewer.ui.geometry import restore_saved_geometry, window_pos_text
from stream_media_viewer.ui.list_row import FACE_MARK, row_marks
from stream_media_viewer.ui.operator_window import OperatorWindow
from stream_media_viewer.ui.output_window import OutputWindow
from stream_media_viewer.ui.overlays import clamp_loupe_px
from stream_media_viewer.ui.panic_keys import PanicKeyFilter
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap
from stream_media_viewer.ui.settings_dialog import SettingsDialog, SettingsDraft


def _format_duration(ms: int) -> str:
    sec = max(0, int(ms) // 1000)
    return f"{sec // 60}:{sec % 60:02d}"


class ProtectThread(QThread):
    done = Signal(object, bool, bool, int)
    failed = Signal(int)

    def __init__(
        self,
        bgr: np.ndarray,
        settings: AppSettings,
        marks: list[dict],
        seq: int,
        *,
        skip_faces: bool = False,
        rotation: int = 0,
        still: bool = False,
    ) -> None:
        super().__init__()
        self._bgr = bgr
        self._still = still
        self._settings = ProtectSettings.of(settings)
        self._marks = marks
        self.seq = seq
        self._skip_faces = skip_faces
        self._rotation = clamp_rotation(rotation)

    def run(self) -> None:
        try:
            note = FileNote(
                marks=self._marks,
                skip_faces=self._skip_faces,
                rotation=self._rotation,
            )
            with PROTECT_LOCK:
                out, faces, texts = protect_for_note(
                    self._bgr, self._settings, note, still=self._still
                )
            if self.isInterruptionRequested():
                return
            if out is None:
                self.failed.emit(self.seq)
                return
            out = enhance_bgr(out, level=self._settings.enhance_level)
            self.done.emit(out, faces, texts, self.seq)
        except Exception as exc:
            log_exception(exc)
            if not self.isInterruptionRequested():
                self.failed.emit(self.seq)


class StreamMediaViewerApp(PrepFlowMixin):
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings if settings is not None else load_settings()
        configure_dev_allow_capture(self.settings.dev_allow_capture)
        self.gate = OutputGate()
        # 待機画像が読めたときだけ待機にする（読めないのに黒い窓を OBS に出さない）
        standby = self._standby_frame()
        self.gate.enable_standby(standby is not None)
        self.operator = OperatorWindow(self.gate)
        self.output = OutputWindow(self.gate)
        self.operator.lang = self.settings.language
        self.operator.retranslate()
        self._items: list[MediaItem] = []
        self._visible: list[int] = []
        self._index = 0
        self._preview: np.ndarray | None = None
        self._source_bgr: np.ndarray | None = None
        self._live: np.ndarray | None = None
        self._worker: ProtectThread | None = None
        self._load_worker: ImageLoadWorker | None = None
        self._prefetch_worker: PrefetchWorker | None = None
        self._prefetch_queue: list[MediaItem] = []
        self._view_gen = 0
        self._load_should_protect = True
        self._protect_cache = ProtectFrameCache()
        self._thumb_pix: dict[str, QPixmap] = {}
        self._scan_worker: ScanWorker | None = None
        self._thumb_worker: ThumbWorker | None = None
        self._kept_threads: list[QThread] = []
        self._pending_thumbs: list[Path] = []
        self._closing = False
        self._scan_token = 0
        self._videos_loaded = False
        self._prepare_after_videos = False
        self._protect_seq = 0
        self._undo: list[list[dict]] = []
        self._false_undo: list[str] = []
        self._shipped_start = set(load_shipped_hashes())
        self._video = VideoPlayer()
        self._video.frame_ready.connect(self._on_video_frame)
        self._video.finished.connect(self._on_video_finished)
        self._playing_to_output = False
        self._face_hold = FaceHold()
        self._live_path = ""
        self._preload: PreloadWorker | None = None
        self._folder_queue: list[MediaItem] = []
        self._folder_total = 0
        # 写真の下準備は自動で少しずつ（見ている写真に近い順。休みながら、手前の作業を優先）
        self._auto = AutoPrepQueue()
        self._auto_item: MediaItem | None = None
        self._auto_started = 0.0
        self._auto_hold = False
        self._auto_timer = QTimer()
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._auto_prep_tick)
        self._face_refresh_timer = QTimer()
        self._face_refresh_timer.setSingleShot(True)
        self._face_refresh_timer.timeout.connect(lambda: self._refresh_list(follow=False))
        self._wire()
        self._restore_checks()
        guard_popups_from_capture(QApplication.instance())
        # 確認や設定の小窓が出ていても、テンキー0で必ず配信から隠す
        self._panic_keys = PanicKeyFilter(self._on_panic, self.operator)
        QApplication.instance().installEventFilter(self._panic_keys)
        if standby is not None and self.gate.window_visible:
            self.output.show_frame(standby)
        self.operator.set_library_ready(False)
        self.operator.set_dates_available(False)
        if self.settings.last_folder:
            self._open_folder_path(self.settings.last_folder)
        else:
            self._show_nothing()
        self._sync_windows()
        self._refresh_prep_label()

    def _wire(self) -> None:
        op = self.operator
        op.open_folder_requested.connect(self._on_folder_button)
        op.recent_folder_requested.connect(self._open_folder_path)
        op.clear_filters_requested.connect(self._clear_filters)
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
        op.prepare_videos_requested.connect(lambda: self._prepare_folder("video"))
        op.clear_marks_requested.connect(self._clear_marks)
        op.brush_width_changed.connect(self._on_brush_width)
        op.slider_loupe.valueChanged.connect(self._on_operator_loupe_px)
        self.output.slider_loupe.valueChanged.connect(self._on_output_loupe_px)
        op.enhance_cycle_requested.connect(self._cycle_enhance)
        op.settings_requested.connect(self._open_settings)
        op.language_cycle_requested.connect(self._cycle_language)
        op.region_clicked.connect(self._on_preview_region)
        op.hide_item_requested.connect(self._toggle_hidden)
        op.audio_changed.connect(self._on_audio_ui)
        op.false_undo_requested.connect(self._undo_false_face)
        op.btn_false_face.toggled.connect(lambda _on=False: self._sync_false_face_button())
        op.rotate_left_requested.connect(lambda: self._rotate_current(270))
        op.rotate_right_requested.connect(lambda: self._rotate_current(90))
        op.timeline.sliderReleased.connect(self._apply_in_out)
        op.timeline_out.sliderReleased.connect(self._apply_in_out)
        op.destroyed.connect(self._on_operator_gone)
        # 操作画面を閉じたら配信用の窓も消す（ソフトを閉じた → 消える）
        op.closing.connect(self._on_panic)
        self.output.hide_requested.connect(self._on_panic)
        op._viewer_app = self
        op.set_live_probe(self._current_is_live)

    def _restore_checks(self) -> None:
        op = self.operator
        op.chk_face.setChecked(self.settings.face_blur)
        op.chk_text.setChecked(self.settings.text_blur)
        self.operator.set_enhance_level(self.settings.enhance_level)
        op.slider_brush.blockSignals(True)
        op.slider_brush.setValue(self.settings.brush_width)
        op.slider_brush.blockSignals(False)
        op.chk_audio.blockSignals(True)
        op.chk_audio.setChecked(self.settings.video_audio)
        op.chk_audio.blockSignals(False)
        op.preview.brush_width = self.settings.brush_width
        op.slider_loupe.blockSignals(True)
        op.slider_loupe.setValue(self.settings.operator_loupe_px)
        op.slider_loupe.blockSignals(False)
        op.preview.set_loupe_px(self.settings.operator_loupe_px)
        self.output.set_loupe_px(self.settings.output_loupe_px)
        op.set_sort(self.settings.list_sort)
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
            # 壊れた・手で直した値でも起動できるように（読めなければ既定の位置）
            restore_saved_geometry(self.operator, self.settings.operator_geometry)
        self.operator.clamp_to_screen()
        restore_saved_geometry(self.output, self.settings.output_pos)

    def _on_settings_ui(self) -> None:
        prev_face = self.settings.face_blur
        self.settings.face_blur = self.operator.chk_face.isChecked()
        self.settings.text_blur = self.operator.chk_text.isChecked()
        self.settings.enhance_level = self.operator.enhance_level
        if prev_face and not self.settings.face_blur:
            self.settings.blur_off_confirmed = False
        self._forget_prepared()
        self._reload_current()

    def _on_filters_ui(self) -> None:
        self.settings.date_from = self.operator.date_from.date().toString("yyyy-MM-dd")
        self.settings.date_to = self.operator.date_to.date().toString("yyyy-MM-dd")
        self.settings.list_sort = self.operator.selected_sort()
        reloaded = self._refresh_list()
        # 動画を足すときは先に読み始める（読み込み中に「合うファイルがない」と出さない）
        self._maybe_load_videos()
        if not reloaded:
            if self._visible and self.operator.showing_guide():
                # 絞り込みで空だった一覧に戻ってきたら、案内のままにせず先頭を確認に出す
                self._select_visible(self._index)
            elif not self._visible and not self._scanning():
                self._show_nothing()
        if self.operator.chk_videos.isChecked() and self._videos_loaded:
            self._start_thumbs()

    def _on_loop_ui(self) -> None:
        item = self._current()
        if item:
            self.settings.note_for(str(item.path)).loop = self.operator.chk_loop.isChecked()

    def _on_audio_ui(self) -> None:
        self.settings.video_audio = self.operator.chk_audio.isChecked()
        enabled = self._playing_to_output and self.settings.video_audio
        self._video.set_audio_enabled(enabled)

    def _cycle_enhance(self) -> None:
        self.settings.enhance_level = next_enhance_level(self.settings.enhance_level)
        self.operator.set_enhance_level(self.settings.enhance_level)
        self._forget_prepared()
        self._reload_current()

    def _tell_error(self, key: str, *, dialog: bool = False) -> None:
        text = t(self.settings.language, key)
        try:
            self.operator.meta.setText(text)
        except RuntimeError:
            pass
        if dialog:
            try:
                QMessageBox.warning(self.operator, "StreamMediaViewer(ぬ)", text)
            except RuntimeError:
                QMessageBox.warning(None, "StreamMediaViewer(ぬ)", text)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            self.operator,
            SettingsDraft(
                blur_strength=self.settings.blur_strength,
                face_blur=self.settings.face_blur,
                text_blur=self.settings.text_blur,
                enhance_level=self.settings.enhance_level,
                language=self.settings.language,
                include_subfolders=self.settings.include_subfolders,
                standby_path=self.settings.standby_path,
                use_standby=self.settings.use_standby,
            ),
            cache_text=self._cache_size_text(),
            clear_cache=self._clear_cache,
        )
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        applied = dialog.draft()
        dialog.deleteLater()
        if not accepted:
            return
        previous = {
            "blur_strength": self.settings.blur_strength,
            "include_subfolders": self.settings.include_subfolders,
            "standby_path": self.settings.standby_path,
            "use_standby": self.settings.use_standby,
        }
        prev_sub = previous["include_subfolders"]
        try:
            self.settings.blur_strength = clamp_blur_strength(applied.blur_strength)
            self.settings.include_subfolders = applied.include_subfolders
            self.settings.standby_path = applied.standby_path
            self.settings.use_standby = applied.use_standby
            standby = self._standby_frame()
            self.gate.enable_standby(standby is not None)
            if standby is not None and self.gate.masked:
                self.output.show_frame(standby)
            self._sync_windows()
            if applied.use_standby and applied.standby_path and standby is None:
                self._tell_error("standby_unreadable", dialog=True)
            if prev_sub != applied.include_subfolders and self.settings.last_folder:
                self._open_folder_path(self.settings.last_folder)
                self._save_settings()
                return
            self._forget_prepared()
            if not self._refresh_list():
                self._reload_current()
            self._save_settings()
        except Exception as exc:
            log_exception(exc)
            for key, value in previous.items():
                setattr(self.settings, key, value)
            self.gate.enable_standby(bool(previous["use_standby"] and previous["standby_path"]))
            self._sync_windows()
            self._tell_error(user_error_key(exc, where="settings"), dialog=True)

    def _standby_frame(self) -> np.ndarray | None:
        """待機画像（1920×1080 に収めた絵）。使わない・読めないときは None。"""
        if not self.settings.use_standby or not self.settings.standby_path:
            return None
        image = load_rgb_image(Path(self.settings.standby_path))
        if image is None:
            return None
        return fit_letterbox(rgb_to_bgr(np.array(image)))

    def _cycle_language(self) -> None:
        self.settings.language = "en" if self.settings.language == "ja" else "ja"
        self.operator.lang = self.settings.language
        self.operator.retranslate()
        self._refresh_list()
        item = self._current()
        if item is not None:
            self.operator.meta.setText(self._item_meta_text(item))
        elif not self._scanning():
            self._show_nothing()
        self._refresh_prep_label()

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
        picked_browse = chosen is not None and chosen is browse
        path = "" if chosen is None or picked_browse else str(chosen.data() or "")
        menu.deleteLater()
        if picked_browse:
            self._browse_folder()
        elif path:
            self._open_folder_path(path)

    def _browse_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self.operator, t(self.settings.language, "pick_folder"), self.settings.last_folder
        )
        if path:
            self._open_folder_path(path)

    def _recent_folders(self, *, exclude: str = "") -> list[str]:
        return [
            path
            for path in self.settings.recent_folders
            if path != exclude and Path(path).is_dir()
        ]

    def _scanning(self) -> bool:
        return _qthread_live(self._scan_worker)

    def _show_nothing(self) -> None:
        """確認できるファイルが無いときの案内。理由ごとに、次にやることのボタンを出す。"""
        op = self.operator
        op.set_media_kind(None)
        op.set_false_face_visible(False)
        if not self.settings.last_folder:
            op.show_start(self._recent_folders())
        elif self._items:
            op.show_filtered_empty()
        else:
            op.show_guide(
                t(self.settings.language, "folder_empty"),
                pick=True,
                recents=self._recent_folders(exclude=self.settings.last_folder),
            )
        op.refresh_status()

    def _clear_filters(self) -> None:
        """絞り込みを全部外す（写真は入れる）。案内の「絞り込みを解除」から。"""
        op = self.operator
        boxes = (op.chk_star_only, op.chk_filter_face, op.chk_dates, op.chk_hidden, op.chk_photos)
        for box in (*boxes, op.combo_place, op.combo_folder):
            box.blockSignals(True)
        for box in boxes[:-1]:
            box.setChecked(False)
        op.chk_photos.setChecked(True)
        op.combo_place.setCurrentIndex(0)
        op.combo_folder.setCurrentIndex(0)
        for box in (*boxes, op.combo_place, op.combo_folder):
            box.blockSignals(False)
        op._sync_date_style()
        self._on_filters_ui()

    def _open_folder_path(self, path: str) -> None:
        self.operator.set_library_ready(True)
        self._auto_hold = False
        self.settings.last_folder = path
        self.settings.recent_folders = remember_folder(self.settings.recent_folders, path)
        self._start_scan(Path(path))

    def _start_scan(
        self,
        folder: Path,
        *,
        kinds: frozenset[str] | None = None,
        replace: bool = True,
    ) -> None:
        if self._closing:
            return
        wanted = frozenset(kinds) if kinds is not None else frozenset({"image"})
        self._scan_token += 1
        token = self._scan_token
        self._view_gen += 1
        self._stop_protect_worker()
        self._stop_load_worker()
        self._stop_prefetch()
        self._stop_qthread(self._scan_worker, timeout_ms=8000)
        self._scan_worker = None
        if replace:
            self._stop_qthread(self._thumb_worker, timeout_ms=8000)
            self._thumb_worker = None
            self._pending_thumbs = []
            self._thumb_pix.clear()
            self._forget_prepared()
            self._items = []
            self._visible = []
            self._index = 0
            self._videos_loaded = False
            self._prepare_after_videos = False
            self._auto_timer.stop()
            # 日付の幅はフォルダごとに作り直すので、前のフォルダの日付の絞り込みは外す
            self.operator.chk_dates.blockSignals(True)
            self.operator.chk_dates.setChecked(False)
            self.operator.chk_dates.blockSignals(False)
            self.operator.set_items([], [])
            self.operator.set_media_kind(None)
            self.operator.show_guide(t(self.settings.language, "scanning"), done=0, total=0)
            self._refresh_prep_label()
        else:
            self.operator.meta.setText(t(self.settings.language, "scanning"))
        worker = ScanWorker(folder, recursive=self.settings.include_subfolders, kinds=wanted)
        worker.progress.connect(lambda done, total, tok=token: self._on_scan_progress(done, total, tok))
        worker.found_items.connect(
            lambda items, tok=token, scan_kinds=wanted, repl=replace: self._on_scan_found(
                items, tok, scan_kinds, repl
            )
        )
        worker.finished_items.connect(
            lambda items, tok=token, scan_kinds=wanted, repl=replace: self._on_scan_done(
                items, tok, scan_kinds, repl
            )
        )
        worker.start()
        self._scan_worker = worker

    def _on_scan_progress(self, done: int, total: int, token: int) -> None:
        if token != self._scan_token:
            return
        # 進み具合は確認欄の案内だけに出す（上の行に同じ数字を重ねない）
        self.operator.set_scan_progress(done, total)

    def _on_scan_found(
        self,
        items: object,
        token: int,
        kinds: frozenset[str],
        replace: bool,
    ) -> None:
        if token != self._scan_token or not replace or self._items:
            return
        incoming = list(items) if isinstance(items, list) else []
        if not incoming:
            return
        self._items = incoming
        self._apply_saved_marks()
        self._apply_folder_dates(reset=True)
        self._index = 0
        self._refresh_list()
        if self._visible:
            self.operator.reveal_preview()
            self._select_visible(0)
            self._start_thumbs()

    def _on_scan_done(
        self,
        items: object,
        token: int,
        kinds: frozenset[str],
        replace: bool,
    ) -> None:
        if token != self._scan_token:
            return
        incoming = list(items) if isinstance(items, list) else []
        current_path = str(self._current().path) if self._current() is not None else None
        if replace:
            self._items = incoming
        else:
            self._items = merge_media_items(self._items, incoming)
        if "video" in kinds:
            self._videos_loaded = True
        self._apply_saved_marks()
        self._apply_folder_dates(reset=replace)
        if replace and current_path is None:
            self._index = 0
        waiting_videos = not self._videos_loaded and (
            self.operator.chk_videos.isChecked() or self._prepare_after_videos
        )
        showing_guide = True
        try:
            showing_guide = self.operator.guide.isVisible()
        except RuntimeError:
            showing_guide = True
        self._refresh_list(keep_path=current_path)
        if current_path:
            if self._visible:
                self.operator.reveal_preview()
        elif self._visible:
            self.operator.reveal_preview()
            if replace or showing_guide:
                self._select_visible(0)
            else:
                current = self._current()
                if current is not None:
                    self.operator.meta.setText(self._item_meta_text(current))
        elif waiting_videos:
            self.operator.show_guide(t(self.settings.language, "scanning"))
        else:
            self._show_nothing()
        self._start_thumbs()
        self._auto_schedule(1000)
        if self._prepare_after_videos and self._videos_loaded:
            self._prepare_after_videos = False
            self._prepare_folder("video")
            return
        self._maybe_load_videos()

    def _maybe_load_videos(self) -> None:
        if self._videos_loaded:
            return
        if not self.operator.chk_videos.isChecked() and not self._prepare_after_videos:
            return
        folder = self.settings.last_folder
        if not folder:
            return
        if self._scan_worker is not None and _qthread_live(self._scan_worker):
            try:
                if self._scan_worker.isRunning():
                    return
            except RuntimeError:
                pass
        self._start_scan(Path(folder), kinds=frozenset({"video"}), replace=False)

    def _start_thumbs(self) -> None:
        if self._closing:
            return
        op = self.operator
        wanted = thumb_paths_for(
            self._items,
            photos=op.chk_photos.isChecked(),
            videos=op.chk_videos.isChecked(),
        )
        wanted = [path for path in wanted if str(path) not in self._thumb_pix]
        wanted = self._thumb_paths_near_current(wanted)
        if self._thumb_worker is not None and _qthread_live(self._thumb_worker):
            try:
                running = self._thumb_worker.isRunning()
            except RuntimeError:
                running = False
            if running:
                for path in wanted:
                    if path not in self._pending_thumbs:
                        self._pending_thumbs.append(path)
                return
        if not wanted:
            self._thumb_worker = None
            self._drain_pending_thumbs()
            return
        self._launch_thumb_worker(wanted)

    def _thumb_paths_near_current(self, paths: list[Path]) -> list[Path]:
        if not self._visible or not paths:
            return paths
        wanted = set(paths)
        ordered: list[Path] = []
        seen: set[Path] = set()
        rows = (self._index, *neighbor_rows(self._index, len(self._visible), radius=12))
        for row in rows:
            if row < 0 or row >= len(self._visible):
                continue
            path = self._items[self._visible[row]].path
            if path in wanted and path not in seen:
                ordered.append(path)
                seen.add(path)
        for path in paths:
            if path not in seen:
                ordered.append(path)
        return ordered

    def _launch_thumb_worker(self, paths: list[Path]) -> None:
        if self._closing or not paths:
            return
        worker = ThumbWorker(paths)
        worker.thumb_ready.connect(self._on_thumb_ready)
        worker.finished.connect(self._on_thumbs_finished)
        worker.start()
        self._thumb_worker = worker

    def _drain_pending_thumbs(self) -> None:
        pending = [path for path in self._pending_thumbs if str(path) not in self._thumb_pix]
        self._pending_thumbs = []
        if pending:
            self._launch_thumb_worker(pending)

    def _on_thumbs_finished(self) -> None:
        self._drain_pending_thumbs()

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
                self.operator.set_row_icon(row, pix, video=self._items[index].kind == "video")
                break

    def _on_operator_gone(self, *_args: object) -> None:
        self.shutdown()

    def shutdown(self) -> None:
        self._closing = True
        for timer in (self._auto_timer, self._face_refresh_timer):
            try:
                timer.stop()
            except RuntimeError:
                # ソフトの終わりぎわは、窓より先にタイマーが消えていることがある
                pass
        self._scan_token += 1
        self._pending_thumbs = []
        try:
            self._video.close()
        except RuntimeError:
            pass
        self._playing_to_output = False
        self._stop_protect_worker(timeout_ms=1500)
        self._stop_load_worker(timeout_ms=1500)
        self._stop_prefetch(timeout_ms=1500)
        self._stop_preload()
        self._stop_qthread(self._scan_worker, timeout_ms=8000)
        self._scan_worker = None
        thumb = self._thumb_worker
        self._stop_qthread(thumb, timeout_ms=8000)
        self._pending_thumbs = []
        if self._thumb_worker is not thumb:
            self._stop_qthread(self._thumb_worker, timeout_ms=8000)
        self._thumb_worker = None
        self._wait_kept_threads(timeout_ms=8000)

    def _keep_qthread(self, worker: QThread | None) -> None:
        self._kept_threads = [item for item in self._kept_threads if _qthread_live(item)]
        if worker is not None and _qthread_live(worker) and worker not in self._kept_threads:
            self._kept_threads.append(worker)

    def _wait_kept_threads(self, *, timeout_ms: int) -> None:
        leftover: list[QThread] = []
        for worker in list(self._kept_threads):
            try:
                if _qthread_live(worker):
                    worker.wait(max(1, int(timeout_ms)))
                if _qthread_live(worker):
                    leftover.append(worker)
            except (RuntimeError, AttributeError):
                continue
        self._kept_threads = leftover

    def _stop_qthread(self, worker, *, timeout_ms: int) -> None:
        if worker is None:
            return
        try:
            if hasattr(worker, "thumb_ready"):
                try:
                    worker.thumb_ready.disconnect(self._on_thumb_ready)
                except (TypeError, RuntimeError):
                    pass
                try:
                    worker.finished.disconnect(self._on_thumbs_finished)
                except (TypeError, RuntimeError):
                    pass
            if hasattr(worker, "finished_items"):
                try:
                    worker.finished_items.disconnect()
                except (TypeError, RuntimeError):
                    pass
                try:
                    worker.progress.disconnect()
                except (TypeError, RuntimeError):
                    pass
            worker.requestInterruption()
            if timeout_ms > 0:
                worker.wait(max(1, int(timeout_ms)))
        except (TypeError, RuntimeError, AttributeError):
            self._keep_qthread(worker)
            return
        self._keep_qthread(worker)

    def _apply_folder_dates(self, *, reset: bool = True) -> None:
        """日付欄の幅をフォルダ内の最古〜最新に合わせる。

        reset=False（動画を足したときなど）は、選んでいた日付を残して幅だけ広げる。
        """
        dates = [item.captured_at.date() for item in self._items if item.captured_at]
        op = self.operator
        if not dates:
            op.set_dates_available(False)
            return
        op.set_dates_available(True)
        start, end = min(dates), max(dates)
        qmin = QDate(start.year, start.month, start.day)
        qmax = QDate(end.year, end.month, end.day)
        keep_from = op.date_from.date()
        keep_to = op.date_to.date()
        op.date_from.blockSignals(True)
        op.date_to.blockSignals(True)
        op.date_from.setDateRange(qmin, qmax)
        op.date_to.setDateRange(qmin, qmax)
        if reset or not op.chk_dates.isChecked():
            op.date_from.setDate(qmin)
            op.date_to.setDate(qmax)
        else:
            op.date_from.setDate(max(qmin, min(keep_from, qmax)))
            op.date_to.setDate(max(qmin, min(keep_to, qmax)))
        op.date_from.blockSignals(False)
        op.date_to.blockSignals(False)
        self.settings.date_from = op.date_from.date().toString("yyyy-MM-dd")
        self.settings.date_to = op.date_to.date().toString("yyyy-MM-dd")

    def _apply_saved_marks(self) -> None:
        for item in self._items:
            note = self.settings.note_for(str(item.path))
            item.has_face = note.has_face and not note.skip_faces
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
            faces=op.chk_filter_face.isChecked(),
            gps_yes=False,
            gps_no=False,
            place=op.selected_place(),
            dates=op.chk_dates.isChecked(),
            date_from=op.date_from.date().toPython(),
            date_to=op.date_to.date().toPython(),
            folder=op.selected_folder(),
            relative_folder=item.relative_folder,
            hidden=note.hidden,
            show_hidden=op.chk_hidden.isChecked(),
        )

    def _refresh_list(self, *, keep_path: str | None = None, follow: bool = True) -> bool:
        """一覧を作り直す。見ていたファイルが一覧から消えたら、表示もそれに合わせる。

        follow=True なら、消えたときに新しい選択（または空の案内）を読み直して True を返す。
        そうしないと、確認画面は前の絵のまま、手動ぼかしや送るは別のファイルに向いてしまう。
        """
        current_path = keep_path or ""
        if not current_path and self._visible:
            current = self._current()
            if current is not None:
                current_path = str(current.path)
        selected_place = self.operator.selected_place()
        selected_folder = self.operator.selected_folder()
        places = sorted({item.place_name for item in self._items if item.place_name})
        folders = sorted({item.relative_folder for item in self._items if item.relative_folder})
        self.operator.set_places(places, selected_place)
        self.operator.set_folders(folders, selected_folder)
        self._items = sorted_items(self._items, self.operator.selected_sort())
        self._visible = [i for i, item in enumerate(self._items) if self._passes_filter(item)]
        labels: list[str] = []
        icons: list[QPixmap | None] = []
        tips: list[str] = []
        rotations: list[int] = []
        visible_items: list[MediaItem] = []
        for i in self._visible:
            item = self._items[i]
            visible_items.append(item)
            labels.append(self._row_label(item))
            icons.append(self._thumb_pix.get(str(item.path)))
            tips.append(self._row_tooltip(item))
            rotations.append(self.settings.note_for(str(item.path)).rotation)
        self.operator.set_items(visible_items, labels, icons, tips, rotations)
        row = 0
        found = False
        if current_path:
            for index, item_index in enumerate(self._visible):
                if str(self._items[item_index].path) == current_path:
                    row = index
                    found = True
                    break
        if self._visible:
            self._index = row
            self.operator.list.blockSignals(True)
            self.operator.list.setCurrentRow(row)
            self.operator.list.blockSignals(False)
        if follow and current_path and not found:
            self._reload_current()
            return True
        return False

    def _row_label(self, item: MediaItem) -> str:
        note = self.settings.note_for(str(item.path))
        # ✓（下準備できた）は動画だけ。写真は自動で下準備するので、印を並べても意味が薄い
        marks = row_marks(
            favorite=note.favorite,
            live=self._live_path == str(item.path) and not self.gate.masked,
            ready=item.kind == "video" and cache_is_ready(self._key_for(item), self._folder_id()),
            manual=bool(note.marks),
            lang=self.settings.language,
        )
        warn = FACE_MARK if item.has_face else ""
        when = item.captured_at.strftime("%m/%d %H:%M") if item.captured_at else ""
        place = item.place_name
        detail = "  ".join(part for part in (marks, when, place, warn) if part)
        return detail

    def _item_meta_text(self, item: MediaItem | None, *, duration_ms: int | None = None) -> str:
        if item is None:
            return ""
        lang = self.settings.language
        parts: list[str] = []
        if item.captured_at:
            parts.append(item.captured_at.strftime("%Y-%m-%d %H:%M"))
        if item.place_name:
            parts.append(item.place_name)
        parts.append(item.path.name)
        if item.relative_folder:
            parts.append(item.relative_folder)
        if item.kind == "video":
            parts.append(t(lang, "kind_video"))
        if duration_ms and duration_ms > 0:
            parts.append(_format_duration(duration_ms))
        if item.has_face:
            parts.append(FACE_MARK)
        note = self.settings.note_for(str(item.path))
        if note.marks:
            parts.append("💧" + t(lang, "btn_manual"))
        return "  ".join(parts)

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

    def _current_is_live(self) -> bool:
        item = self._current()
        return bool(item and self._live_path == str(item.path) and not self.gate.masked)

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
        self._face_hold.reset()
        self._playing_to_output = False
        self.operator.set_playing(False)
        self.gate.begin_load()
        # 前のファイルの処理結果が、次のファイルの確認画面・キャッシュに入らないようにする。
        self._protect_seq += 1
        self._stop_protect_worker()
        self._preview = None
        self._source_bgr = None
        if item is None:
            if not self._scanning():
                self._show_nothing()
            self.operator.set_false_face_visible(False)
            self.operator.refresh_status()
            return
        self.operator.reveal_preview()
        note = self.settings.note_for(str(item.path))
        self.operator.chk_loop.blockSignals(True)
        self.operator.chk_loop.setChecked(note.loop)
        self.operator.chk_loop.blockSignals(False)
        self.operator._set_manual(bool(note.marks))
        self.operator.btn_star.setChecked(note.favorite)
        self.operator.meta.setText(self._item_meta_text(item))
        self.operator.meta.setToolTip(str(item.path))
        self.operator.set_media_kind(item.kind)
        self._sync_false_face_button()
        if item.kind == "image":
            self._source_bgr = None
            self._stop_load_worker()
            self._stop_prefetch()
            self._view_gen += 1
            gen = self._view_gen
            cached = self._cached_protect_frame(item)
            if cached is not None:
                self._load_should_protect = False
                self._protect_seq += 1
                self._on_protected(*cached, self._protect_seq)
                return
            self._load_should_protect = True
            prefix = self._item_meta_text(item)
            self.operator.meta.setText(f"{prefix} · {t(self.settings.language, 'processing')}")
            worker = ImageLoadWorker(item.path, gen)
            worker.loaded.connect(self._on_image_loaded)
            worker.failed.connect(self._on_image_load_failed)
            worker.start()
            self._load_worker = worker
            return
        fps = self._video.open(str(item.path))
        duration = self._video.duration_ms()
        self.operator.timeline.setRange(0, max(1, duration))
        self.operator.timeline_out.setRange(0, max(1, duration))
        self.operator.timeline.setValue(note.in_ms)
        self.operator.timeline_out.setValue(note.out_ms if note.out_ms else duration)
        self._video.in_ms = note.in_ms
        self._video.out_ms = note.out_ms
        self._video.loop = note.loop
        self.operator.meta.setText(self._item_meta_text(item, duration_ms=duration))
        frame = self._video.seek_ms(note.in_ms)
        if frame is None:
            self._mark_unreadable(item)
            return
        if self._video.last_raw is not None:
            self._source_bgr = self._video.last_raw
        else:
            self._source_bgr = frame
        raw = self._source_bgr
        self._show_operator_frame(rotate_bgr(raw, note.rotation))
        self._start_protect(raw, note.marks)
        _ = fps

    def _show_operator_frame(self, bgr: np.ndarray) -> None:
        self.operator.preview.set_frame(bgr_to_pixmap(bgr), smooth=False)

    def _on_image_loaded(self, bgr: object, seq: int) -> None:
        if seq != self._view_gen:
            return
        if not isinstance(bgr, np.ndarray):
            return
        item = self._current()
        if item is None or item.kind != "image":
            return
        self._source_bgr = bgr
        note = self.settings.note_for(str(item.path))
        if self._load_should_protect:
            self._show_operator_frame(rotate_bgr(bgr, note.rotation))
            self._start_protect(bgr, note.marks)

    def _on_image_load_failed(self, seq: int) -> None:
        if seq != self._view_gen:
            return
        item = self._current()
        if item is not None:
            self._mark_unreadable(item)

    def _stop_load_worker(self, timeout_ms: int = 0) -> None:
        worker = self._load_worker
        self._load_worker = None
        if worker is None:
            return
        try:
            worker.loaded.disconnect(self._on_image_loaded)
            worker.failed.disconnect(self._on_image_load_failed)
        except (TypeError, RuntimeError):
            pass
        self._stop_qthread(worker, timeout_ms=timeout_ms)

    def _cached_protect_frame(self, item: MediaItem) -> tuple[np.ndarray, bool, bool] | None:
        key = self._key_for(item)
        hit = self._protect_cache.get(key)
        if hit is not None:
            return hit
        loaded = read_protected_image(self._folder_id(), key)
        if loaded is None:
            return None
        self._protect_cache.put(key, loaded[0], loaded[1], loaded[2])
        return loaded

    def _mark_unreadable(self, item: MediaItem) -> None:
        item.readable = False
        self._preview = None
        self.operator.set_media_kind(None)
        self.operator.meta.setText(t(self.settings.language, "unreadable"))
        self._refresh_list(follow=False)
        self.operator.list.blockSignals(True)
        self.operator.list.setCurrentRow(-1)
        self.operator.list.blockSignals(False)
        self.operator.refresh_status()

    def _start_protect(self, bgr: np.ndarray, marks: list[dict]) -> None:
        self._protect_seq += 1
        seq = self._protect_seq
        self._stop_protect_worker()
        # 手動ぼかし・回転を足した直後に、足す前の絵を送れないようにする。
        self.gate.begin_load()
        self._preview = None
        self.operator.refresh_status()
        item = self._current()
        skip = bool(item and self.settings.note_for(str(item.path)).skip_faces)
        rotation = 0
        if item is not None:
            rotation = self.settings.note_for(str(item.path)).rotation
            cached = self._cached_protect_frame(item)
            if cached is not None:
                self._on_protected(*cached, seq)
                return
        prefix = self._item_meta_text(item) if item else ""
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, 'processing')}")
        self._worker = ProtectThread(
            bgr,
            self.settings,
            list(marks),
            seq,
            skip_faces=skip,
            rotation=rotation,
            still=bool(item and item.kind == "image"),
        )
        self._worker.done.connect(self._on_protected)
        self._worker.failed.connect(self._on_protect_failed)
        self._worker.start()

    def _stop_protect_worker(self, timeout_ms: int = 0) -> None:
        worker = self._worker
        if worker is None:
            return
        try:
            worker.done.disconnect(self._on_protected)
            worker.failed.disconnect(self._on_protect_failed)
        except (TypeError, RuntimeError):
            pass
        self._stop_qthread(worker, timeout_ms=timeout_ms)
        self._worker = None

    def _on_protect_failed(self, seq: int) -> None:
        if seq != self._protect_seq:
            return
        self._preview = None
        self._tell_error("protect_failed")
        self.operator.refresh_status()

    def _on_protected(self, bgr: np.ndarray, has_face: bool, has_text: bool, seq: int) -> None:
        if seq != self._protect_seq:
            return
        item = self._current()
        if item:
            note = self.settings.note_for(str(item.path))
            if note.skip_faces:
                has_face = False
            item.has_face = has_face
            item.has_text_region = has_text
            note.has_face = has_face
            note.has_text_region = has_text
            self._protect_cache.put(self._key_for(item), bgr, has_face, has_text)
            if item.kind == "image":
                key = self._key_for(item)
                folder_id = self._folder_id()
                if not cache_is_ready(key, folder_id):
                    write_protected_image(
                        folder_id,
                        key,
                        bgr,
                        has_face=has_face,
                        has_text=has_text,
                    )
            duration = self.operator.timeline.maximum() if item.kind == "video" else None
            self.operator.meta.setText(self._item_meta_text(item, duration_ms=duration))
        fitted = fit_letterbox(bgr)
        self._preview = fitted
        self.operator.reveal_preview()
        try:
            self.operator.preview.set_frame(bgr_to_pixmap(bgr))
        except Exception as exc:
            log_exception(exc)
            self._preview = None
            self._tell_error("protect_failed")
            return
        self.gate.mark_processed()
        self.operator.refresh_status()
        self._relabel_current_row()
        self._sync_false_face_button()
        item = self._current()
        if item and item.kind == "video" and not self._folder_queue:
            self._start_preload()
            # 写真の自動の下準備は、この動画の下準備が終わるまで待ってから続く
            self._auto_schedule(PAUSE_POLL_MS)
        if item and item.kind == "image":
            self._prefetch_neighbors()

    def _on_send(self) -> None:
        if self._preview is None:
            return
        item = self._current()
        preview = self._preview
        # 顔ありの写真は毎回ひと呼吸おいて、ぼかしが足りているか見てもらう（Enter でそのまま出せる）
        if item and item.kind == "image" and item.has_face and self.settings.face_blur:
            if not self._ask_send("confirm_faces"):
                return
        if not self.settings.face_blur and not self.settings.blur_off_confirmed:
            if not self._ask_send("confirm_no_blur"):
                return
            self.settings.blur_off_confirmed = True
        # 確認のあいだに裏の処理で見ているファイルや確認用の絵が変わったら、確認していない絵は送らない
        if self._current() is not item or self._preview is not preview:
            return
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
            self._video.set_audio_enabled(self.settings.video_audio)
            self._playing_to_output = True
            self._bind_cache(item)
            cached = cache_is_ready(self._key_for(item), self._folder_id())
            if not cached and abs(self._video.position_ms() - note.in_ms) > 120:
                self._video.seek_ms(note.in_ms)
            self._video.play()
            self.operator.set_playing(True)
        self._sync_windows()
        self.operator.refresh_status()
        self._sync_live_marks()

    def _ask_send(self, key: str) -> bool:
        """送る前の確認。ボタンは「配信に出す」（Enter）と「やめる」（Esc）。"""
        lang = self.settings.language
        box = QMessageBox(self.operator)
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(t(lang, key))
        send = box.addButton(t(lang, "confirm_send"), QMessageBox.ButtonRole.AcceptRole)
        cancel = box.addButton(t(lang, "confirm_cancel"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(send)
        box.setEscapeButton(cancel)
        box.exec()
        chosen = box.clickedButton()
        box.deleteLater()
        return chosen is send

    def _protect_sync(self, frame: np.ndarray, marks: list[dict]) -> np.ndarray:
        item = self._current()
        note = self.settings.note_for(str(item.path)) if item else None
        if note is None:
            out, _, _ = protect_frame_safe(
                frame,
                face_blur=self.settings.face_blur,
                text_blur=self.settings.text_blur,
                marks=marks,
                strength=self.settings.blur_strength,
                false_face_hashes=self.settings.all_false_face_hashes(),
                pipeline=self.settings.face_pipeline,
                face_hold=self._face_hold,
            )
        else:
            out, _, _ = protect_for_note(
                frame, self.settings, note, face_hold=self._face_hold
            )
        if out is None:
            raise RuntimeError("protect failed")
        out = enhance_bgr(out, level=self.settings.enhance_level)
        return out

    def _on_video_frame(self, frame: np.ndarray) -> None:
        try:
            self.operator.preview.set_frame(bgr_to_pixmap(frame), smooth=False)
        except Exception as exc:
            log_exception(exc)
            self._tell_error("protect_failed")
            return
        if self._playing_to_output and self.gate.window_visible:
            fitted = fit_letterbox(frame)
            self._live = fitted
            self.output.show_frame(fitted)

    def _on_video_finished(self) -> None:
        self._playing_to_output = False
        self.operator.set_playing(False)

    def _toggle_play(self) -> None:
        item = self._current()
        if item is None or item.kind != "video":
            return
        note = self.settings.note_for(str(item.path))
        if self._video.playing:
            self._video.pause()
            self.operator.set_playing(False)
            return
        self._video.set_protect(lambda frame: self._protect_sync(frame, note.marks))
        item = self._current()
        self._playing_to_output = bool(
            item and self._live_path == str(item.path) and not self.gate.masked
        )
        self._video.set_audio_enabled(self._playing_to_output and self.settings.video_audio)
        if item:
            self._bind_cache(item)
        self._video.seek_ms(note.in_ms)
        self._video.play()
        self.operator.set_playing(True)

    def _on_panic(self) -> None:
        self._video.pause()
        self._playing_to_output = False
        self.operator.set_playing(False)
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

    def _sync_false_face_button(self) -> None:
        item = self._current()
        if item is None:
            self.operator.set_false_face_visible(False)
            self.operator.set_false_undo_visible(False)
            self.operator.preview.setToolTip("")
            return
        note = self.settings.note_for(str(item.path))
        self.operator.set_false_face_visible(bool(item.has_face and not note.skip_faces))
        self.operator.set_false_undo_visible(bool(self._false_undo))
        if item.has_face and not note.skip_faces and self.operator.btn_false_face.isChecked():
            self.operator.preview.setToolTip(t(self.settings.language, "false_face"))
        else:
            self.operator.preview.setToolTip("")

    def _rotate_current(self, step: int) -> None:
        item = self._current()
        if item is None:
            return
        note = self.settings.note_for(str(item.path))
        turn = clamp_rotation(step)
        if turn == 0:
            return
        source = self._ensure_source_bgr()
        if item.kind == "video" and self._video.last_raw is not None:
            source = self._video.last_raw
            self._source_bgr = source
        aspect = None
        if source is not None and source.shape[0] > 0 and source.shape[1] > 0:
            # 手動ぼかしは今の向きの絵の上の位置。回す前の向きの 幅÷高さ を渡す
            height, width = source.shape[:2]
            if note.rotation in (90, 270):
                width, height = height, width
            aspect = width / height
        note.rotation = clamp_rotation(note.rotation + turn)
        note.marks = rotate_marks(note.marks, turn, aspect=aspect)
        self._forget_prepared()
        self._undo = []
        if item.kind == "video":
            # フォルダの下準備の途中なら止めない（止めると列が進まなくなる）。
            # 動いている分は始めたときの向きの鍵で作るので、新しい向きの絵と混ざらない。
            if not self._folder_queue:
                self._stop_preload()
            self._video.set_protect(lambda frame, marks=note.marks: self._protect_sync(frame, marks))
        if source is not None:
            self._show_operator_frame(rotate_bgr(source, note.rotation))
        self._reprotect_current()
        self.operator.set_row_rotation(self.operator.list.currentRow(), note.rotation)
        self._save_settings()

    def _reprotect_current(self) -> None:
        item = self._current()
        if item is None:
            return
        note = self.settings.note_for(str(item.path))
        source = self._ensure_source_bgr()
        if item.kind == "video" and self._video.last_raw is not None:
            source = self._video.last_raw
            self._source_bgr = source
        if source is None:
            self._reload_current()
            return
        self._forget_prepared()
        self._start_protect(source, note.marks)
        self._relabel_current_row()
        self._sync_false_face_button()

    def _ensure_source_bgr(self) -> np.ndarray | None:
        if self._source_bgr is not None:
            return self._source_bgr
        item = self._current()
        if item is None or item.kind != "image":
            return None
        image = load_rgb_image(item.path)
        if image is None:
            return None
        self._source_bgr = rgb_to_bgr(np.array(image))
        return self._source_bgr

    def _toggle_hidden(self, row: int) -> None:
        if row < 0 or row >= len(self._visible):
            return
        item = self._items[self._visible[row]]
        note = self.settings.note_for(str(item.path))
        note.hidden = not note.hidden
        # 見ているファイルが一覧から消えたときだけ読み直す（配信中の動画を止めない）。
        self._refresh_list()

    def _on_preview_region(self, nx: float, ny: float) -> None:
        if self.operator.preview.mode != "off":
            return
        if self.operator.btn_false_face.isChecked() and self._reject_false_at(nx, ny):
            return
        self._toggle_play()

    def _reject_false_at(self, nx: float, ny: float) -> bool:
        item = self._current()
        if item is None or not item.has_face:
            return False
        note = self.settings.note_for(str(item.path))
        if note.skip_faces:
            return False
        source = self._ensure_source_bgr()
        if source is None:
            return False
        oriented = rotate_bgr(source, note.rotation)
        boxes = detect_face_boxes(
            oriented,
            false_face_hashes=self.settings.all_false_face_hashes(),
            pipeline=self.settings.face_pipeline,
            still=item.kind == "image",
        )
        height, width = oriented.shape[:2]
        hit = face_box_at(boxes, nx, ny, width, height)
        if hit is None:
            return False
        before = set(self.settings.all_false_face_hashes())
        learned = remember_false_faces(
            self.settings.all_false_face_hashes(), oriented, [hit]
        )
        added = [digest for digest in learned if digest not in before]
        self._false_undo.extend(added)
        try_update_shipped_catalog(learned)
        bundled = set(load_shipped_hashes())
        self.settings.false_face_hashes = [item for item in learned if item not in bundled]
        self._forget_prepared()
        self._reprotect_current()
        self._save_settings()
        self._sync_false_face_button()
        return True

    def _undo_false_face(self) -> None:
        if not self._false_undo:
            return
        digest = self._false_undo.pop()
        self.settings.false_face_hashes = [
            item for item in self.settings.false_face_hashes if item != digest
        ]
        try_remove_shipped_hash(digest, protected=self._shipped_start)
        self._forget_prepared()
        self._reprotect_current()
        self._save_settings()
        self._sync_false_face_button()

    def _add_mark(self, mark: dict) -> None:
        item = self._current()
        if not item:
            return
        note = self.settings.note_for(str(item.path))
        self._undo.append(list(note.marks))
        self._undo = self._undo[-10:]
        note.marks.append(mark)
        self._reprotect_current()

    def _undo_mark(self) -> None:
        item = self._current()
        if not item or not self._undo:
            return
        self.settings.note_for(str(item.path)).marks = self._undo.pop()
        self._reprotect_current()

    def _clear_marks(self) -> None:
        item = self._current()
        if not item:
            return
        note = self.settings.note_for(str(item.path))
        if not note.marks:
            return
        self._undo.append(list(note.marks))
        self._undo = self._undo[-10:]
        note.marks = []
        self._reprotect_current()

    def _on_brush_width(self, value: int) -> None:
        self.settings.brush_width = clamp_brush_width(value)
        self.operator.preview.brush_width = self.settings.brush_width

    def _on_operator_loupe_px(self, value: int) -> None:
        self.settings.operator_loupe_px = clamp_loupe_px(value)

    def _on_output_loupe_px(self, value: int) -> None:
        self.settings.output_loupe_px = clamp_loupe_px(value)

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

    def _sync_windows(self) -> None:
        self.output.refresh()
        self.operator.refresh_status()

    def show(self) -> None:
        self.operator.show()
        self._sync_windows()
        self.operator.raise_()
        self.operator.activateWindow()

    def persist(self) -> None:
        try:
            self._on_operator_gone()
        except RuntimeError:
            pass
        try:
            geo = self.operator.saveGeometry()
            self.settings.operator_geometry = geo.toHex().data().decode("ascii")
            self.settings.output_pos = window_pos_text(self.output)
        except RuntimeError:
            pass
        self._save_settings()

    def _save_settings(self) -> None:
        try:
            save_settings(self.settings)
        except OSError as exc:
            log_exception(exc)
            self._tell_error(user_error_key(exc, where="save"))


def run() -> int:
    install_excepthook()
    try:
        configure_process_identity()
        qt_app = QApplication.instance() or QApplication(sys.argv)
        qt_app.setApplicationName("StreamMediaViewer")
        qt_app.setApplicationDisplayName("StreamMediaViewer(ぬ)")
        apply_app_icon(qt_app)
        settings, load_error = load_settings_with_error()
        app = StreamMediaViewerApp(settings)
        qt_app.aboutToQuit.connect(app.persist)
        # 配信用の窓が出ていても、操作画面を閉じたらソフトを終える
        app.operator.closing.connect(qt_app.quit)
        app.show()
        if load_error:
            app._tell_error(load_error, dialog=True)
        return qt_app.exec()
    except Exception as exc:
        log_exception(exc)
        configure_process_identity()
        qt_app = QApplication.instance() or QApplication(sys.argv)
        apply_app_icon(qt_app)
        QMessageBox.critical(
            None,
            "StreamMediaViewer(ぬ)",
            t("ja", user_error_key(exc, where="startup")),
        )
        return 1
