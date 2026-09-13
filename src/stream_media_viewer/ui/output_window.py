"""OBS 取り込み用の配信出力ウィンドウ。既定は全黒マスク。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.safety.output_gate import OutputGate


class OutputWindow(QMainWindow):
    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.setWindowTitle(OUTPUT_WINDOW_TITLE)
        self.resize(1280, 720)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = QLabel()
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setMinimumSize(640, 360)
        layout.addWidget(self.canvas)
        self.setCentralWidget(root)
        self.refresh()

    def refresh(self) -> None:
        # 配信画面には状態もファイル名も出さない
        self.canvas.setText("")
        if self._gate.masked:
            self.canvas.setStyleSheet("background: #000000;")
        else:
            self.canvas.setStyleSheet("background: #101010;")
