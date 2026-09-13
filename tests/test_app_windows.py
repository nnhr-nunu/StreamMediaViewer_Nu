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
    app.operator.chk_faces.setChecked(True)
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
    assert bar.indexOf(app.operator.btn_brush) < bar.indexOf(app.operator.btn_play)
    assert bar.indexOf(app.operator.btn_play) < bar.indexOf(app.operator.btn_prep)


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
    assert app.operator.btn_play.x() > app.operator.btn_brush.x()


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
