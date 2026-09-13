"""OBS 取り込み用。未送信・緊急は隠す。文字は出さない。"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.render.canvas import OUTPUT_HEIGHT, OUTPUT_WIDTH
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.ui.overlays import OUTPUT_LOUPE_PX, paint_laser, paint_loupe
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap

# 隠しているときタイトルを変える。OBS が「窓なし」と判定し、最後の絵を保持しにくくする。
IDLE_WINDOW_TITLE = "SMV-Output-idle"


class OutputCanvas(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: #000000;")
        self.setMouseTracking(True)
        self._source = QPixmap()
        self._mouse = QPoint(-1, -1)
        self._loupe = False
        self._laser = True
        self.setCursor(Qt.CursorShape.BlankCursor)

    def set_loupe(self, on: bool) -> None:
        self._loupe = bool(on)
        self.update()

    def set_frame_pixmap(self, pix: QPixmap) -> None:
        self._source = pix
        self.setPixmap(pix)
        self.setText("")
        self.update()

    def clear_frame(self) -> None:
        self._source = QPixmap()
        self.clear()
        self.setPixmap(QPixmap())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._mouse = event.position().toPoint()
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._mouse = QPoint(-1, -1)
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._mouse.x() < 0:
            return
        painter = QPainter(self)
        box = self.contentsRect()
        pix = self._source if not self._source.isNull() else (self.pixmap() or QPixmap())
        if self._loupe and not pix.isNull():
            paint_loupe(painter, pix, box, self._mouse, diameter=OUTPUT_LOUPE_PX)
        if self._laser:
            paint_laser(painter, self._mouse)


class OutputWindow(QMainWindow):
    hide_requested = Signal()

    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.setWindowTitle(OUTPUT_WINDOW_TITLE)
        self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = OutputCanvas()
        layout.addWidget(self.canvas)
        self.setCentralWidget(root)
        self.refresh()

    def set_loupe(self, on: bool) -> None:
        self.canvas.set_loupe(on)

    def show_frame(self, bgr: np.ndarray) -> None:
        pix = bgr_to_pixmap(bgr)
        self.canvas.set_frame_pixmap(pix)

    def closeEvent(self, event) -> None:  # noqa: N802
        event.ignore()
        self.hide_requested.emit()

    def refresh(self) -> None:
        self.canvas.setText("")
        if self._gate.window_visible:
            self.setWindowTitle(OUTPUT_WINDOW_TITLE)
            self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
            self.show()
            return
        self.canvas.clear_frame()
        self.setWindowTitle(IDLE_WINDOW_TITLE)
        self.hide()
