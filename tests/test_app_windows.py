from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer import (
    OPERATOR_WINDOW_TITLE,
    OUTPUT_WINDOW_TITLE,
    __version__,
    display_version,
)
from stream_media_viewer.app import ProtectThread, StreamMediaViewerApp
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
            video_audio=False,
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


def test_photo_and_video_show_different_controls(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    app.operator.set_media_kind("image")
    assert app.operator.btn_play.isHidden()
    assert app.operator.btn_prep.isHidden()
    assert app.operator.timeline.isHidden()
    assert app.operator.chk_loop.isHidden()
    app.operator.set_media_kind("video")
    assert not app.operator.btn_play.isHidden()
    assert not app.operator.btn_prep.isHidden()
    assert not app.operator.timeline.isHidden()
    assert not app.operator.chk_loop.isHidden()
    bar = app.operator.btn_prev.parentWidget().layout()
    assert bar.indexOf(app.operator.btn_next) < bar.indexOf(app.operator.btn_send)
    assert bar.indexOf(app.operator.btn_manual) < bar.indexOf(app.operator.btn_rot_left)
    assert bar.indexOf(app.operator.btn_rot_left) < bar.indexOf(app.operator.btn_rot_right)
    assert bar.indexOf(app.operator.btn_rot_right) < bar.indexOf(app.operator.btn_play)
    assert bar.indexOf(app.operator.btn_play) < bar.indexOf(app.operator.btn_prep)
    assert bar.indexOf(app.operator.btn_prep) < bar.indexOf(app.operator.btn_false_face)
    assert bar.indexOf(app.operator.btn_false_face) < bar.indexOf(app.operator.btn_lang)
    assert bar.indexOf(app.operator.btn_lang) < bar.indexOf(app.operator.btn_help)


def test_common_buttons_stay_put_when_video_controls_appear(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    app.operator.resize(1280, 800)
    app.operator.show()
    qtbot.waitExposed(app.operator)
    app.operator.set_media_kind("image")
    qtbot.wait(20)
    next_x = app.operator.btn_next.x()
    send_x = app.operator.btn_send.x()
    panic_x = app.operator.btn_panic.x()
    app.operator.set_media_kind("video")
    qtbot.wait(20)
    assert app.operator.btn_next.x() == next_x
    assert app.operator.btn_send.x() == send_x
    assert app.operator.btn_panic.x() == panic_x
    assert app.operator.btn_play.x() > app.operator.btn_manual.x()


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
    assert "04/01" in label
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
    clicked: list[bool] = []
    canvas.clicked.connect(lambda: clicked.append(True))
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(120, 90))
    assert clicked


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
    assert not hasattr(op, "chk_faces")
    assert op.filter_box.layout().indexOf(op.combo_sort) == -1
    assert op.sort_box.layout().indexOf(op.combo_sort) >= 0
    assert op.combo_sort.count() == 3
    assert "事前処理" in op.btn_folder_prep.text()
    assert "事前処理データ" in op.btn_clear_cache.text()
    assert op.chk_star_only.text() == "⭐"
    assert op.manual_tools.isHidden()
    op._set_manual(True)
    assert not op.manual_tools.isHidden()
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
    assert op.minimumWidth() >= 900
    assert op.minimumHeight() >= 560
    assert op.btn_false_face.isHidden()
    op.set_false_face_visible(True)
    assert not op.btn_false_face.isHidden()
    assert "誤検出修正" in op.btn_false_face.text()
    assert "左90" in op.btn_rot_left.text()
    assert "右90" in op.btn_rot_right.text()
    op.show_guide("読み込み中…", done=1, total=4)
    assert not op.scan_progress.isHidden()
    assert op.scan_count.text() == "1 / 4"
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
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    item = MediaItem(path=Path("face.jpg"), kind="image", captured_at=None, has_gps=False, has_face=True)
    label = app._row_label(item)
    assert "顔あり" in label
    assert "⚠" not in label
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
    lay = app.operator.filter_box.layout()
    assert lay.indexOf(app.operator.chk_dates) == lay.indexOf(app.operator.date_from) - 1
    assert lay.indexOf(app.operator.date_from) == lay.indexOf(app.operator.date_to) - 1


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
