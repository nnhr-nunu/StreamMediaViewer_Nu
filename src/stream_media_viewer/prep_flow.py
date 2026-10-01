"""下準備（ぼかしの作り置き）と先読みの配線。StreamMediaViewerApp に混ぜて使う。

- 写真: 前後の数枚を先に作り、そのあとフォルダ全体を自動で少しずつ作る（休みながら）
- 動画: 選んだ動画は自動。フォルダの動画は 🎦 でまとめて
- 配信へは出さない（作った絵は「送る」まで確認と作り置きにしか使わない）
"""

from __future__ import annotations

import time

import cv2
import numpy as np
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox, QWidget

from stream_media_viewer.errors import log_exception
from stream_media_viewer.i18n import t
from stream_media_viewer.library.auto_prep import PAUSE_POLL_MS, rest_ms
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.neighbors import PREFETCH_RADIUS, neighbor_rows
from stream_media_viewer.library.preview_load import PrefetchWorker
from stream_media_viewer.library.scan import video_header_ok
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
    read_protected_image,
)


def qthread_live(worker: QThread | None) -> bool:
    if worker is None:
        return False
    try:
        return not worker.isFinished()
    except (RuntimeError, AttributeError):
        return False


class PrepFlowMixin:
    """下準備と先読み。状態（_auto など）は StreamMediaViewerApp.__init__ で作る。"""

    # --- 写真の先読み（前後の数枚） ---

    def _stop_prefetch(self, timeout_ms: int = 0) -> None:
        self._prefetch_queue = []
        try:
            self._auto_timer.stop()
        except RuntimeError:
            pass
        self._auto.inflight = False
        worker = self._prefetch_worker
        self._prefetch_worker = None
        if worker is None:
            return
        for slot in (self._on_prefetch_ready, self._on_auto_ready):
            try:
                worker.ready.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        self._stop_qthread(worker, timeout_ms=timeout_ms)

    def _prefetch_neighbors(self) -> None:
        if self._folder_queue or not self._visible:
            return
        self._auto_rebuild()
        folder_id = self._folder_id()
        queued: list[MediaItem] = []
        for row in neighbor_rows(self._index, len(self._visible), radius=PREFETCH_RADIUS):
            item = self._items[self._visible[row]]
            if item.kind != "image":
                continue
            key = self._key_for(item)
            if self._protect_cache.has(key):
                continue
            if cache_is_ready(key, folder_id):
                if self._protect_cache.room() > 0:
                    loaded = read_protected_image(folder_id, key)
                    if loaded is not None:
                        self._protect_cache.put(key, loaded[0], loaded[1], loaded[2])
                continue
            queued.append(item)
        self._prefetch_queue = queued
        if self._prefetch_worker is not None and qthread_live(self._prefetch_worker):
            return
        self._kick_prefetch()

    def _kick_prefetch(self) -> None:
        current = self._current()
        folder_id = self._folder_id()
        while self._prefetch_queue:
            item = self._prefetch_queue.pop(0)
            if current is not None and item.path == current.path:
                continue
            key = self._key_for(item)
            if self._protect_cache.has(key) or cache_is_ready(key, folder_id):
                continue
            note = self.settings.note_for(str(item.path))
            worker = PrefetchWorker(item.path, self.settings, note, key, folder_id)
            worker.ready.connect(self._on_prefetch_ready)
            self._keep_qthread(self._prefetch_worker)
            worker.start()
            self._prefetch_worker = worker
            return
        self._keep_qthread(self._prefetch_worker)
        self._prefetch_worker = None
        # 前後の分が済んだら、残りの写真を自動で少しずつ
        self._auto_schedule(rest_ms(0, live=False))

    def _on_prefetch_ready(self, key: str, bgr: object, faces: bool, texts: bool) -> None:
        if isinstance(bgr, np.ndarray):
            if self._protect_cache.room() > 0:
                self._protect_cache.put(key, bgr, bool(faces), bool(texts))
            self._apply_prefetch_marks(key, bool(faces), bool(texts))
        self._kick_prefetch()

    def _apply_prefetch_marks(self, key: str, faces: bool, texts: bool) -> None:
        # 先読みは現在の行の近くから。近い行から探し、その行だけ書き直す（全行は重い）。
        total = len(self._visible)
        near = list(neighbor_rows(self._index, total, radius=PREFETCH_RADIUS))
        near_set = set(near)
        order = near + [row for row in range(total) if row not in near_set]
        for row in order:
            if row < 0 or row >= total:
                continue
            item = self._items[self._visible[row]]
            if item.kind != "image" or self._key_for(item) != key:
                continue
            self._set_found_marks(item, faces, texts)
            list_item = self.operator.list.item(row)
            if list_item is not None:
                list_item.setText(self._row_label(item))
            return

    def _set_found_marks(self, item: MediaItem, faces: bool, texts: bool) -> None:
        item.has_face = item.has_face or faces
        item.has_text_region = item.has_text_region or texts
        note = self.settings.note_for(str(item.path))
        note.has_face = item.has_face
        note.has_text_region = item.has_text_region

    def _forget_prepared(self) -> None:
        """設定が変わって、手元の作り置きの絵が使えなくなったとき。"""
        self._protect_cache.clear()
        self._auto.forget()

    # --- 写真の下準備（フォルダ全体を自動で、休みながら） ---

    def _auto_rebuild(self) -> None:
        visible = [self._items[i] for i in self._visible]
        visible_paths = {str(item.path) for item in visible}
        # 一覧に出ていない写真も後回しで作る（😊の絞り込みで顔ありを見つけられるように）
        others = [
            item
            for item in self._items
            if str(item.path) not in visible_paths
            and not self.settings.note_for(str(item.path)).hidden
        ]
        self._auto.rebuild(visible, self._index, others)
        self._refresh_prep_label()

    def _auto_schedule(self, delay_ms: int) -> None:
        if self._closing or self._auto_hold or not self.settings.last_folder:
            return
        try:
            # 操作画面が出ていない（閉じかけ・起動前）ときは裏の作業を始めない
            if not self.operator.isVisible():
                return
            self._auto_timer.start(max(0, int(delay_ms)))
        except RuntimeError:
            return

    def _auto_paused(self) -> bool:
        """手前の作業がある間は止める。写真の切り替えや動画の再生を遅くしないため。"""
        if self._folder_queue or self._video.playing:
            return True
        busy = (
            self._preload,
            self._worker,
            self._load_worker,
            self._prefetch_worker,
            self._scan_worker,
            self._thumb_worker,
        )
        return any(qthread_live(worker) for worker in busy)

    def _auto_prep_tick(self) -> None:
        if self._closing or self._auto_hold:
            return
        if self._auto_paused():
            self._auto_timer.start(PAUSE_POLL_MS)
            return
        folder_id = self._folder_id()
        item = self._auto.take_next(lambda it: self._auto_is_ready(it, folder_id))
        if item is None:
            self._refresh_prep_label()
            if self._auto.pending:
                # 済んでいるか確かめる途中。操作画面を止めないよう、続きは次の回に
                self._auto_timer.start(0)
            return
        note = self.settings.note_for(str(item.path))
        worker = PrefetchWorker(item.path, self.settings, note, self._key_for(item), folder_id)
        worker.ready.connect(self._on_auto_ready)
        self._auto.inflight = True
        self._auto_item = item
        self._auto_started = time.monotonic()
        worker.start(QThread.Priority.LowestPriority)
        self._prefetch_worker = worker
        self._refresh_prep_label()

    def _auto_is_ready(self, item: MediaItem, folder_id: str) -> bool:
        key = self._key_for(item)
        return self._protect_cache.has(key) or cache_is_ready(key, folder_id)

    def _on_auto_ready(self, key: str, bgr: object, faces: bool, texts: bool) -> None:
        elapsed = time.monotonic() - self._auto_started
        self._auto.inflight = False
        item = self._auto_item
        self._auto_item = None
        if item is not None:
            # 作れなかった写真も、何度も繰り返さない（見たときに作り直す）
            self._auto.mark_done(item)
        self._keep_qthread(self._prefetch_worker)
        self._prefetch_worker = None
        if isinstance(bgr, np.ndarray) and item is not None:
            had_face = item.has_face
            self._set_found_marks(item, bool(faces), bool(texts))
            self._relabel_path(str(item.path))
            if item.has_face and not had_face and self.operator.chk_filter_face.isChecked():
                # 😊で絞っているとき、新しく見つかった顔ありを一覧に足す（まとめて少し後で）
                self._face_refresh_timer.start(2000)
        self._refresh_prep_label()
        self._auto_schedule(rest_ms(elapsed, live=self.gate.window_visible))

    def _relabel_path(self, path: str) -> None:
        for row, index in enumerate(self._visible):
            item = self._items[index]
            if str(item.path) != path:
                continue
            list_item = self.operator.list.item(row)
            if list_item is not None:
                list_item.setText(self._row_label(item))
            return

    def _refresh_prep_label(self) -> None:
        lang = self.settings.language
        done, total = self._auto.progress()
        if not self.settings.last_folder or total <= 0 or self._auto_hold:
            text = ""
        elif done >= total:
            text = t(lang, "photo_prep_done")
        else:
            text = t(lang, "photo_prep_running").format(done=done, total=total)
        self.operator.set_prep_text(text)

    # --- 作り置きの鍵 ---

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
            skip_faces=note.skip_faces,
            false_face_hashes=self.settings.all_false_face_hashes(),
            rotation=note.rotation,
            face_pipeline=self.settings.face_pipeline,
            still=item.kind == "image",
        )

    def _folder_id(self) -> str:
        folder = self.settings.last_folder or "_none"
        return folder_cache_id(folder)

    # --- 動画の下準備 ---

    def _bind_cache(self, item: MediaItem) -> None:
        key = self._key_for(item)
        folder_id = self._folder_id()
        if cache_is_ready(key, folder_id):
            meta = read_meta(key, folder_id)
            self._video.set_cache(cache_folder(key, folder_id), float(meta.get("fps") or 30))
            return
        self._video.set_cache(None, 30)

    def _stop_preload(self) -> None:
        worker = self._preload
        self._preload = None
        self._stop_qthread(worker, timeout_ms=1500)

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
                self._set_found_marks(item, has_face, has_text)
                break
        prefix = self.operator.meta.text().split(" · ")[0]
        label_key = "prepared" if cache_is_ready(key, folder_id) else "protect_failed"
        self.operator.meta.setText(f"{prefix} · {t(self.settings.language, label_key)}")
        self._refresh_list()
        self._advance_folder_queue()

    def _advance_folder_queue(self) -> None:
        if not self._folder_queue:
            self._refresh_list()
            self._auto_schedule(PAUSE_POLL_MS)
            return
        self._folder_queue.pop(0)
        if not self._folder_queue:
            self._refresh_list()
            self._auto_schedule(PAUSE_POLL_MS)
            return
        self._start_preload_for(self._folder_queue[0])

    def _prepare_folder(self, kind: str = "video") -> None:
        """フォルダの動画をまとめて下準備する（写真は自動で進むので、ここは動画だけ）。"""
        if kind == "video" and not self._videos_loaded:
            if not self.settings.last_folder:
                return
            self._prepare_after_videos = True
            self._maybe_load_videos()
            return
        if not self._items:
            return
        lang = self.settings.language
        pending: list[MediaItem] = []
        total_bytes = 0
        for item in self._items:
            if item.kind != kind:
                continue
            if cache_is_ready(self._key_for(item), self._folder_id()):
                continue
            pending.append(item)
            note = self.settings.note_for(str(item.path))
            duration_ms = 0
            fps = 30.0
            if item.kind == "video":
                frames = 0.0
                if video_header_ok(item.path):
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
            QMessageBox.information(self.operator, "", t(lang, "prepared_videos_all"))
            return
        ask = t(lang, "prepare_videos_ask").format(size=format_bytes(total_bytes))
        if QMessageBox.question(self.operator, "", ask) != QMessageBox.StandardButton.Yes:
            return
        self._stop_preload()
        self._stop_prefetch()
        self._folder_queue = pending
        self._folder_total = len(pending)
        self._start_preload_for(pending[0])

    # --- 下準備データの削除（設定から） ---

    def _cache_size_text(self) -> str:
        folder = format_bytes(cache_size_bytes(self._folder_id()))
        total = format_bytes(cache_size_bytes())
        return t(self.settings.language, "cache_size").format(folder=folder, total=total)

    def _clear_cache(self, parent: QWidget | None = None) -> str:
        """消すか聞いてから消す。消したあとの容量の文を返す（設定の画面に出す）。"""
        lang = self.settings.language
        folder_size = format_bytes(cache_size_bytes(self._folder_id()))
        total_size = format_bytes(cache_size_bytes())
        ask = t(lang, "clear_cache_ask").format(folder=folder_size, total=total_size)
        box = QMessageBox(parent or self.operator)
        box.setText(ask)
        this_btn = box.addButton(t(lang, "clear_this_folder"), QMessageBox.ButtonRole.AcceptRole)
        all_btn = box.addButton(t(lang, "clear_all_cache"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(t(lang, "cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        box.deleteLater()
        if clicked is not this_btn and clicked is not all_btn:
            return self._cache_size_text()
        self._stop_preload()
        self._stop_prefetch()
        self._folder_queue = []
        if clicked is this_btn:
            clear_folder_cache(self._folder_id())
        else:
            clear_preload_cache()
        self._video.set_cache(None, 30)
        self._forget_prepared()
        # 消した直後に作り直すと消した意味がないので、次にフォルダを開くまで自動は休む
        self._auto_hold = True
        self._refresh_prep_label()
        self._refresh_list()
        return self._cache_size_text()
