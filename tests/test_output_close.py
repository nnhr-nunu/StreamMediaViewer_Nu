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
