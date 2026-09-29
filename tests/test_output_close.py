import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut

from stream_media_viewer.app import StreamMediaViewerApp
from stream_media_viewer.safety.output_gate import OutputGate, OutputReason
from stream_media_viewer.settings import AppSettings
from stream_media_viewer.ui.output_window import OutputWindow


def _send_black(app: StreamMediaViewerApp) -> None:
    app.gate.mark_processed()
    app._preview = np.zeros((1080, 1920, 3), dtype=np.uint8)
    app._on_send()


def test_closing_the_operator_hides_the_output(qtbot) -> None:
    # ソフトを閉じたら配信用の窓は消える。送ったまま操作画面だけ閉じても、絵を残さない。
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    app.show()
    _send_black(app)
    assert app.output.isVisible()
    app.operator.close()
    assert app.gate.reason is OutputReason.PANIC
    assert not app.output.isVisible()


def test_output_window_lets_the_app_quit(qtbot) -> None:
    # ソフトを終えるときの close（人の × ではない）は拒まない。拒むと窓だけ残って終われない。
    gate = OutputGate()
    window = OutputWindow(gate)
    qtbot.addWidget(window)
    gate.mark_processed()
    gate.send_to_output()
    window.refresh()
    assert window.isVisible()
    assert not window.testAttribute(Qt.WidgetAttribute.WA_QuitOnClose)
    assert window.close()
    assert not window.isVisible()


def test_output_window_has_its_own_panic_keys(qtbot) -> None:
    # ⦿・🔍 を押して配信用の窓が前にあっても、Esc／0 で隠せる。
    window = OutputWindow(OutputGate())
    qtbot.addWidget(window)
    keys = {shortcut.key().toString() for shortcut in window.findChildren(QShortcut)}
    assert {"Esc", "0"} <= keys
    hits: list[int] = []
    window.hide_requested.connect(lambda: hits.append(1))
    for shortcut in window.findChildren(QShortcut):
        shortcut.activated.emit()
    assert len(hits) == 2


def test_unreadable_standby_image_keeps_the_output_hidden(qtbot, tmp_path) -> None:
    # 待機画像が消えた・画像でないときに、黒い 1920×1080 の窓を OBS に出さない
    broken = tmp_path / "gone.png"
    settings = AppSettings(use_standby=True, standby_path=str(broken))
    app = StreamMediaViewerApp(settings)
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    app.show()
    assert app.gate.reason is OutputReason.STARTUP
    assert not app.output.isVisible()


def test_popups_from_the_operator_are_kept_out_of_capture(qtbot, monkeypatch) -> None:
    # ツールチップ・メニューなど別の窓にもファイル名が出る。配信用の窓だけは取り込ませる。
    import sys

    from PySide6.QtWidgets import QApplication, QMenu

    from stream_media_viewer.ui import capture_exclude

    if sys.platform != "win32":
        return
    excluded: list[object] = []
    monkeypatch.setattr(capture_exclude, "exclude_from_capture", lambda w: excluded.append(w))
    capture_exclude.guard_popups_from_capture(QApplication.instance())
    menu = QMenu()
    qtbot.addWidget(menu)
    menu.addAction("a.jpg")
    menu.popup(menu.pos())
    qtbot.waitUntil(lambda: menu in excluded, timeout=2000)
    menu.hide()
    output = OutputWindow(OutputGate())
    qtbot.addWidget(output)
    output.show()
    qtbot.waitExposed(output)
    assert output not in excluded


def test_rotating_a_video_does_not_stall_the_folder_prep(qtbot, monkeypatch, tmp_path) -> None:
    # フォルダの動画の下準備の途中で動画を回しても、下準備の列を止めない
    from stream_media_viewer.library.item import MediaItem

    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    clip = MediaItem(path=tmp_path / "clip.mp4", kind="video", captured_at=None, has_gps=False)
    other = MediaItem(path=tmp_path / "next.mp4", kind="video", captured_at=None, has_gps=False)
    app._items = [clip, other]
    app._visible = [0, 1]
    app._index = 0
    app._folder_queue = [other]
    stops: list[int] = []
    monkeypatch.setattr(app, "_stop_preload", lambda: stops.append(1))
    app._rotate_current(90)
    assert stops == []
    assert app.settings.note_for(str(clip.path)).rotation == 90
