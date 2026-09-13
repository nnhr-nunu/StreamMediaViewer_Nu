"""OBS 取り込み用。未送信・緊急は隠す。文字は出さない。"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.render.canvas import OUTPUT_HEIGHT, OUTPUT_WIDTH
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap

# 隠しているときタイトルを変える。OBS が「窓なし」と判定し、最後の絵を保持しにくくする。
IDLE_WINDOW_TITLE = "StreamMediaViewer(ぬ) - idle"


class OutputWindow(QMainWindow):
    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.setWindowTitle(OUTPUT_WINDOW_TITLE)
        self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = QLabel()
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setStyleSheet("background: #000000;")
        layout.addWidget(self.canvas)
        self.setCentralWidget(root)
        self.refresh()

    def show_frame(self, bgr: np.ndarray) -> None:
        pix = bgr_to_pixmap(bgr)
        self.canvas.setPixmap(pix)
        self.canvas.setText("")

    def refresh(self) -> None:
        self.canvas.setText("")
        if self._gate.window_visible:
            self.setWindowTitle(OUTPUT_WINDOW_TITLE)
            self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
            self.show()
            return
        self.canvas.clear()
        self.canvas.setPixmap(QPixmap())
        self.setWindowTitle(IDLE_WINDOW_TITLE)
        self.hide()
