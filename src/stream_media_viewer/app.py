"""2 ウィンドウ起動。配信側はゲートが開けるまで黒画面。"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.settings import load_settings, save_settings
from stream_media_viewer.ui.operator_window import OperatorWindow
from stream_media_viewer.ui.output_window import OutputWindow


class StreamMediaViewerApp:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.gate = OutputGate()
        self.operator = OperatorWindow(self.gate)
        self.output = OutputWindow(self.gate)
        self.operator.send_requested.connect(self._on_send)
        self.operator.panic_requested.connect(self._on_panic)
        self.operator.panic_cleared.connect(self._on_clear_panic)
        self.operator.destroyed.connect(self.output.close)

    def _sync(self) -> None:
        self.operator.refresh_status()
        self.output.refresh()

    def _on_send(self) -> None:
        self.gate.send_to_output()
        self._sync()

    def _on_panic(self) -> None:
        self.gate.panic()
        self._sync()

    def _on_clear_panic(self) -> None:
        self.gate.clear_panic()
        self._sync()

    def show(self) -> None:
        self.output.show()
        self.operator.show()
        self.operator.raise_()
        self.operator.activateWindow()

    def persist(self) -> None:
        save_settings(self.settings)


def run() -> int:
    qt_app = QApplication.instance() or QApplication(sys.argv)
    app = StreamMediaViewerApp()
    qt_app.aboutToQuit.connect(app.persist)
    app.show()
    return qt_app.exec()
