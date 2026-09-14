import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtWidgets import QDialog, QLabel

from stream_media_viewer import (
    OPERATOR_WINDOW_TITLE,
    OUTPUT_WINDOW_TITLE,
    __version__,
    display_version,
)
from stream_media_viewer.app import ProtectThread, StreamMediaViewerApp
from stream_media_viewer.i18n import t
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.scan import scan_folder
from stream_media_viewer.settings import AppSettings
from stream_media_viewer.ui.output_window import IDLE_WINDOW_TITLE
from stream_media_viewer.ui.settings_dialog import SettingsDialog, SettingsDraft


def test_two_windows_start_hidden(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    assert app.operator.windowTitle() == OPERATOR_WINDOW_TITLE
    assert app.output.windowTitle() == IDLE_WINDOW_TITLE
    assert app.gate.window_visible is False
    app.gate.begin_load()
    app.gate.mark_processed()
    app.gate.send_to_output()
    app._sync_windows()
    assert app.gate.window_visible is True
    assert app.output.windowTitle() == OUTPUT_WINDOW_TITLE
    app._on_panic()
    assert app.gate.window_visible is False
    assert app.output.windowTitle() == IDLE_WINDOW_TITLE


def test_operator_shows_guide_version_stays_in_settings(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    shown = display_version()
    assert __version__ in shown
    assert not hasattr(app.operator, "version_label")
    assert "フォルダを選択" in app.operator.guide.text()
    assert app.operator.btn_play.isHidden()
    assert "次" in app.operator.btn_next.text()
    dialog = SettingsDialog(
        None,
        SettingsDraft(
            blur_strength=25,
            face_blur=True,
            text_blur=False,
            enhance_level="weak",
            language="ja",
        ),
    )
    qtbot.addWidget(dialog)
    assert shown in dialog.version_label.text()
    assert shown not in app.output.windowTitle()
    assert shown not in (app.output.canvas.text() or "")


def test_folder_load_applies_saved_face_marks(qtbot, tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    settings = AppSettings()
    settings.note_for(str(tmp_path / "good.jpg")).has_face = True
    app = StreamMediaViewerApp(settings)
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    app._items = scan_folder(tmp_path)
    app._apply_saved_marks()
    app._refresh_list()
    assert app._items[0].has_face is True
    assert len(app._visible) == 1


def test_hidden_items_leave_the_default_list(qtbot, tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    settings = AppSettings()
    settings.note_for(str(tmp_path / "good.jpg")).hidden = True
    app = StreamMediaViewerApp(settings)
    qtbot.addWidget(app.operator)
    app._items = scan_folder(tmp_path)
    app._refresh_list()
    assert app._visible == []
    app.operator.chk_hidden.setChecked(True)
    assert len(app._visible) == 1


def test_unreadable_video_is_dropped_from_list(qtbot, tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    (tmp_path / "broken.mp4").write_bytes(b"not-a-video")
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    app._open_folder_path(str(tmp_path))
    qtbot.waitUntil(lambda: any(item.path.name == "good.jpg" for item in app._items), timeout=8000)
    qtbot.waitUntil(
        lambda: "broken.mp4"
        not in [app._items[i].path.name for i in app._visible],
        timeout=8000,
    )
    visible_names = [app._items[i].path.name for i in app._visible]
    assert "broken.mp4" not in visible_names
    assert any(item.path.name == "good.jpg" for item in app._items)


def test_protect_thread_emits_failed_on_bad_frame(qtbot) -> None:
    thread = ProtectThread(np.zeros((0, 0, 3), dtype=np.uint8), AppSettings(), [], 1)
    failed: list[bool] = []
    thread.failed.connect(lambda _seq: failed.append(True))
    thread.start()
    qtbot.waitUntil(lambda: not thread.isRunning(), timeout=5000)
    assert failed


def test_persist_failure_does_not_raise(qtbot, monkeypatch) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("stream_media_viewer.app.save_settings", boom)
    app.persist()
    assert t("ja", "save_failed") in app.operator.meta.text()


def test_second_protect_waits_for_the_first(qtbot, monkeypatch) -> None:
    current = {"n": 0, "max": 0}
    lock = threading.Lock()

    def fake_protect(bgr, settings, note, **_kwargs):
        with lock:
            current["n"] += 1
            current["max"] = max(current["max"], current["n"])
        time.sleep(0.15)
        with lock:
            current["n"] -= 1
        return bgr.copy(), False, False

    monkeypatch.setattr("stream_media_viewer.app.protect_for_note", fake_protect)
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    frame = np.zeros((48, 48, 3), dtype=np.uint8)
    app._start_protect(frame, [])
    first = app._worker
    assert first is not None
    app._start_protect(frame, [])
    assert app._worker is not first
    assert not first.isRunning()
    assert current["max"] == 1
    qtbot.waitUntil(lambda: app._worker is not None and not app._worker.isRunning(), timeout=8000)


def test_stop_protect_keeps_running_thread(qtbot, monkeypatch) -> None:
    release = threading.Event()

    def blocker(bgr, settings, note, **_kwargs):
        release.wait(timeout=30)
        return bgr.copy(), False, False

    monkeypatch.setattr("stream_media_viewer.app.protect_for_note", blocker)
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    first = None
    try:
        app._start_protect(np.zeros((48, 48, 3), dtype=np.uint8), [])
        first = app._worker
        assert first is not None
        qtbot.waitUntil(first.isRunning, timeout=2000)
        app._stop_protect_worker(timeout_ms=50)
        assert not first.isFinished()
        assert first in app._kept_threads
    finally:
        release.set()
        if first is not None:
            first.wait(5000)


def test_settings_apply_error_stays_on_operator(qtbot, monkeypatch) -> None:
    app = StreamMediaViewerApp(AppSettings(blur_strength=40))
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    shown: list[str] = []

    class FakeDialog:
        def exec(self) -> QDialog.DialogCode:
            return QDialog.DialogCode.Accepted

        def draft(self) -> SettingsDraft:
            return SettingsDraft(
                blur_strength=200,
                face_blur=True,
                text_blur=False,
                enhance_level="weak",
                language="ja",
            )

    monkeypatch.setattr("stream_media_viewer.app.SettingsDialog", lambda *_a, **_k: FakeDialog())
    monkeypatch.setattr(
        app,
        "_reload_current",
        lambda: (_ for _ in ()).throw(RuntimeError("apply boom")),
    )
    monkeypatch.setattr(
        "stream_media_viewer.app.QMessageBox.warning",
        lambda *a, **k: shown.append(a[2] if len(a) > 2 else k.get("text", "")),
    )
    app._open_settings()
    assert app.settings.blur_strength == 40
    assert t("ja", "settings_apply_failed") in app.operator.meta.text()
    assert shown
    assert t("ja", "settings_apply_failed") in shown[0]


def test_photo_and_video_show_different_controls(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    app.operator.set_media_kind("image")
    assert app.operator.btn_play.isHidden()
    assert app.operator.btn_prep.isHidden()
    assert app.operator.timeline.isHidden()
    assert app.operator.chk_loop.isHidden()
    assert app.operator.chk_audio.isHidden()
    app.operator.set_media_kind("video")
    assert not app.operator.btn_play.isHidden()
    assert not app.operator.btn_prep.isHidden()
    assert not app.operator.timeline.isHidden()
    assert not app.operator.chk_loop.isHidden()
    assert not app.operator.chk_audio.isHidden()
    assert app.operator.chk_audio.isChecked()
    bar = app.operator.btn_prev.parentWidget().layout()
    assert bar.indexOf(app.operator.btn_next) < bar.indexOf(app.operator.btn_send)
    assert bar.indexOf(app.operator.btn_manual) < bar.indexOf(app.operator.btn_rot_left)
    assert bar.indexOf(app.operator.btn_rot_left) < bar.indexOf(app.operator.btn_rot_right)
    assert bar.indexOf(app.operator.btn_rot_right) < bar.indexOf(app.operator.btn_loupe)
    assert bar.indexOf(app.operator.btn_loupe) < bar.indexOf(app.operator.btn_play)
    assert bar.indexOf(app.operator.btn_play) < bar.indexOf(app.operator.btn_prep)
    assert bar.indexOf(app.operator.btn_prep) < bar.indexOf(app.operator.btn_false_face)
    assert bar.indexOf(app.operator.btn_false_face) < bar.indexOf(app.operator.btn_lang)
    assert bar.indexOf(app.operator.btn_lang) < bar.indexOf(app.operator.btn_help)


def test_common_buttons_stay_put_when_video_controls_appear(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    op = app.operator
    op.resize(1280, 800)
    op.show()
    qtbot.waitExposed(op)
    op.set_media_kind("image")
    qtbot.waitUntil(lambda: op.btn_next.width() > 0, timeout=2000)
    next_x = op.btn_next.x()
    send_x = op.btn_send.x()
    panic_x = op.btn_panic.x()
    op.set_media_kind("video")
    qtbot.waitUntil(lambda: not op.btn_play.isHidden() and op.btn_play.width() > 0, timeout=2000)
    assert op.btn_next.x() == next_x
    assert op.btn_send.x() == send_x
    assert op.btn_panic.x() == panic_x
    assert op.btn_play.x() > op.btn_manual.x()


def test_list_caption_omits_filename_and_shows_place(qtbot) -> None:
    from datetime import datetime

    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    item = MediaItem(
        path=Path("C:/secret/trip_DSC01234.jpg"),
        kind="image",
        captured_at=datetime(2024, 4, 1, 12, 0),
        has_gps=True,
        place_name="京都",
    )
    label = app._row_label(item)
    assert "DSC01234" not in label
    assert "京都" in label
    assert "04/01 12:00" in label
    assert "\n京都" not in label
    meta = app._item_meta_text(item)
    assert "DSC01234" in meta
    assert "京都" in meta
    assert "写真" not in meta
    video = MediaItem(path=Path("C:/secret/clip.mp4"), kind="video", captured_at=None, has_gps=False)
    assert "動画" in app._item_meta_text(video)
    tip = app._row_tooltip(item)
    assert "DSC01234" in tip
    assert "京都" in tip


def test_preview_click_toggles_play_on_video(qtbot) -> None:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QPixmap

    from stream_media_viewer.ui.preview_canvas import PreviewCanvas

    canvas = PreviewCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(240, 180)
    canvas.show()
    pix = QPixmap(240, 180)
    pix.fill(Qt.GlobalColor.black)
    canvas.set_frame(pix)
    canvas.click_toggles_play = True
    hits: list[tuple[float, float]] = []
    canvas.region_clicked.connect(lambda x, y: hits.append((x, y)))
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(120, 90))
    assert hits


def test_preview_norm_maps_center_of_pixmap(qtbot) -> None:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QPixmap

    from stream_media_viewer.ui.preview_canvas import PreviewCanvas

    canvas = PreviewCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(400, 300)
    canvas.show()
    qtbot.waitExposed(canvas)
    pix = QPixmap(200, 100)
    pix.fill(Qt.GlobalColor.black)
    canvas.set_frame(pix)
    box = canvas._content_rect()
    mid = QPoint(box.center().x(), box.center().y())
    mapped = canvas._norm(mid)
    assert mapped is not None
    nx, ny = mapped
    assert abs(nx - 0.5) < 0.08
    assert abs(ny - 0.5) < 0.08


def test_operator_ux_labels_and_overlays(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    op = app.operator
    assert not hasattr(op, "btn_standby")
    assert "絞り込み" in op.filter_box.title()
    assert op.btn_star.isCheckable()
    assert "手動ぼかし" in op.btn_manual.text()
    assert "💧" in op.btn_manual.text()
    assert not hasattr(op, "chk_gps")
    assert op.chk_filter_face.text() == "😊"
    lay = op.filter_box.layout()
    assert lay.indexOf(op.chk_star_only) < lay.indexOf(op.chk_filter_face)
    assert lay.indexOf(op.chk_filter_face) < lay.indexOf(op.chk_photos)
    assert lay.indexOf(op.chk_photos) < lay.indexOf(op.chk_videos)
    assert lay.indexOf(op.date_group) < lay.indexOf(op.chk_hidden)
    assert op.lbl_date_range.text() == "～"
    assert op.chk_hidden.text() == "非表示"
    assert op.date_from.maximumWidth() <= 132
    assert op.filter_box.layout().indexOf(op.combo_sort) == -1
    assert op.sort_box.layout().indexOf(op.combo_sort) >= 0
    assert op.combo_sort.count() == 3
    assert "写真" in op.btn_prep_photos.text()
    assert "動画" in op.btn_prep_videos.text()
    assert "自動補正" in op.btn_enhance.text()
    assert "標準" in op.btn_enhance.text()
    assert "拡大" in op.btn_loupe.text()
    assert "事前処理データ" in op.btn_clear_cache.text()
    assert op.chk_star_only.text() == "⭐"
    assert op.loupe_tools.isHidden()
    assert op.manual_tools.isHidden()
    op._set_manual(True)
    assert not op.manual_tools.isHidden()
    assert op.loupe_tools.isHidden()
    op._apply_loupe(True)
    assert not op.loupe_tools.isHidden()
    assert op.manual_tools.isHidden()
    assert op.preview.mode == "off"
    op._set_manual(True)
    assert not op.manual_tools.isHidden()
    assert op.loupe_tools.isHidden()
    assert op.preview.mode == "rect"
    tools = op.manual_tools.layout()
    assert tools.indexOf(op.btn_rect) < tools.indexOf(op.btn_brush)
    assert tools.indexOf(op.btn_brush) < tools.indexOf(op.lbl_brush)
    assert tools.indexOf(op.lbl_brush) < tools.indexOf(op.slider_brush)
    assert tools.indexOf(op.slider_brush) < tools.indexOf(op.btn_undo)
    assert op.slider_brush.isHidden()
    op._tool("stroke")
    assert op.preview.mode == "stroke"
    assert not op.slider_brush.isHidden()
    assert "キー説明" in op.btn_help.text()
    assert "あ/A" in op.btn_lang.text()
    dialog = op._shortcuts_dialog()
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "キー説明"
    body = dialog.findChild(QLabel, "shortcutsBody")
    assert body is not None
    assert "←" in body.text()
    assert "→" in body.text()
    assert "非表示にする" in body.text()
    assert "右下" in body.text()
    assert op.minimumWidth() >= 900
    assert op.minimumHeight() >= 560
    assert op.btn_false_face.isHidden()
    op.set_false_face_visible(True)
    assert not op.btn_false_face.isHidden()
    assert op.btn_false_face.isCheckable()
    assert "誤検出修正" in op.btn_false_face.text()
    assert "OFF" in op.btn_false_face.text()
    op.btn_false_face.setChecked(True)
    assert "ON" in op.btn_false_face.text()
    op.set_playing(True)
    assert "停止" in op.btn_play.text()
    op.set_playing(False)
    assert "再生" in op.btn_play.text()
    assert "左90" in op.btn_rot_left.text()
    assert "右90" in op.btn_rot_right.text()
    op.show_guide("読み込み中…", done=1, total=4)
    assert not op.scan_progress.isHidden()
    assert op.scan_count.text() == "1 / 4"
    op.show_guide("読み込み中…", done=0, total=0)
    assert "0 / 0" not in op.scan_count.text()
    assert "0 / 1" not in op.scan_count.text()
    op.set_places(["京都"], "")
    assert op.combo_place.findData("__none__") >= 0


def test_folder_dates_span_oldest_to_newest(qtbot) -> None:
    from datetime import datetime

    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    app._items = [
        MediaItem(path=Path("a.jpg"), kind="image", captured_at=datetime(2024, 1, 2), has_gps=False),
        MediaItem(path=Path("b.jpg"), kind="image", captured_at=datetime(2024, 5, 9), has_gps=False),
        MediaItem(path=Path("c.jpg"), kind="image", captured_at=None, has_gps=False),
    ]
    app._apply_folder_dates()
    assert app.operator.date_from.date().toString("yyyy-MM-dd") == "2024-01-02"
    assert app.operator.date_to.date().toString("yyyy-MM-dd") == "2024-05-09"
    assert app.operator.chk_dates.isChecked() is False


def test_row_label_says_has_face_not_warning(qtbot) -> None:
    from datetime import datetime

    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    item = MediaItem(
        path=Path("face.jpg"),
        kind="image",
        captured_at=datetime(2024, 9, 13, 21, 5),
        has_gps=False,
        has_face=True,
        place_name="京都",
    )
    label = app._row_label(item)
    assert "😊" in label
    assert "顔あり" not in label
    assert "⚠" not in label
    assert "09/13 21:05" in label
    assert "京都" in label
    app.settings.note_for(str(item.path)).marks = [{"kind": "rect", "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}]
    assert "💧手動ぼかし" in app._row_label(item)


def test_hide_keeps_send_enabled_when_ready(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    app.gate.begin_load()
    app.gate.mark_processed()
    assert app.gate.send_to_output() is True
    app.operator.refresh_status()
    app._on_panic()
    assert app.operator.btn_send.isEnabled()
    assert app.gate.send_to_output() is True


def test_date_checkbox_sits_left_of_date_fields(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    lay = app.operator.date_group.layout()
    assert lay.indexOf(app.operator.chk_dates) == lay.indexOf(app.operator.date_from) - 1
    assert lay.indexOf(app.operator.date_from) == lay.indexOf(app.operator.lbl_date_range) - 1
    assert lay.indexOf(app.operator.lbl_date_range) == lay.indexOf(app.operator.date_to) - 1
    assert app.operator.filter_box.layout().indexOf(app.operator.date_group) < (
        app.operator.filter_box.layout().indexOf(app.operator.chk_hidden)
    )


def test_list_grows_to_two_thumbs_when_wide(qtbot) -> None:
    from PySide6.QtGui import QPixmap

    from stream_media_viewer.ui.list_thumb import with_video_mark

    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    op = app.operator
    op.resize(1280, 800)
    op.show()
    qtbot.waitExposed(op)
    op._relayout_list()
    assert op.list.isWrapping() is True
    grid = op.list.gridSize().width()
    assert op.list.maximumWidth() >= grid * 2
    assert op.list.maximumWidth() <= int((op.width() - 24) * 0.42) + 8
    icon_1280 = op.list.iconSize().width()
    op.resize(1920, 900)
    op._relayout_list()
    assert op.list.iconSize().width() > icon_1280
    badge = with_video_mark(None, 80)
    assert badge.width() == 80
    assert not badge.isNull()
    pix = QPixmap(80, 80)
    marked = with_video_mark(pix, 80)
    assert marked.width() == 80


def test_output_chrome_and_offscreen_send_keeps_position(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    out = app.output
    assert out.btn_loupe.isCheckable()
    assert out.btn_laser.isCheckable()
    assert out.btn_pan.isCheckable()
    assert out.btn_zoom_in.text() == "＋"
    assert out.btn_zoom_out.text() == "－"
    assert out.slider_loupe.isHidden()
    out.btn_loupe.setChecked(True)
    assert not out.slider_loupe.isHidden()
    assert out.canvas._loupe is True
    out.slider_loupe.setValue(200)
    assert out.canvas.loupe_px == 200
    out.btn_laser.setChecked(True)
    assert out.canvas._laser is True
    out.btn_pan.setChecked(True)
    assert out.canvas._pan_mode is True
    assert out.canvas.view_scale == 1.0
    out.btn_zoom_in.click()
    assert out.canvas.view_scale > 1.0
    out.move(-420, 40)
    pos = out.pos()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    out.show_frame(frame)
    assert out.pos() == pos
    top = app.operator.btn_folder.parentWidget().layout()
    assert top.indexOf(app.operator.btn_loupe) < 0
    out.show()
    qtbot.waitExposed(out)
    assert out._zoom_chrome.height() < 400
    assert out._zoom_chrome.height() < out.height() / 2


def test_persist_survives_deleted_workers(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)

    class Dead:
        def isRunning(self) -> bool:
            raise RuntimeError("libshiboken: Internal C++ object (ThumbWorker) already deleted.")

        def isFinished(self) -> bool:
            raise RuntimeError("libshiboken: Internal C++ object (ThumbWorker) already deleted.")

        def requestInterruption(self) -> None:
            return None

        def wait(self, _timeout: int) -> bool:
            return True

        class _Sig:
            def disconnect(self, *_args: object, **_kwargs: object) -> None:
                raise RuntimeError("gone")

        thumb_ready = _Sig()

    app._thumb_worker = Dead()
    app.persist()
