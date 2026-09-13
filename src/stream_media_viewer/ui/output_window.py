"""OBS 取り込み用。未送信・緊急は隠す。文字は出さない。"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.render.canvas import OUTPUT_HEIGHT, OUTPUT_WIDTH
from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.ui.overlays import (
    MAX_LOUPE_PX,
    MIN_LOUPE_PX,
    OUTPUT_LOUPE_PX,
    clamp_loupe_px,
    paint_laser,
    paint_loupe,
)
from stream_media_viewer.ui.pixmaps import bgr_to_pixmap
from stream_media_viewer.ui.styles import DARK_QSS
from stream_media_viewer.ui.view_transform import dest_rect, stepped_view_scale
from stream_media_viewer.ui.win_present import redraw_hwnd

IDLE_WINDOW_TITLE = "SMV-Output-idle"


def _chrome_button(text: str, *, checkable: bool = False) -> QToolButton:
    button = QToolButton()
    button.setObjectName("outputChrome")
    button.setText(text)
    button.setCheckable(checkable)
    button.setAutoRaise(True)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setCursor(Qt.CursorShape.ArrowCursor)
    return button


class OutputCanvas(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: #000000;")
        self.setMouseTracking(True)
        self._source = QPixmap()
        self._mouse = QPoint(-1, -1)
        self._loupe = False
        self._loupe_px = OUTPUT_LOUPE_PX
        self._laser = False
        self._pan_mode = False
        self._scale = 1.0
        self._pan = QPoint(0, 0)
        self._drag_from: QPoint | None = None
        self._pan_from = QPoint(0, 0)
        self._sync_cursor()

    def set_loupe(self, on: bool) -> None:
        self._loupe = bool(on)
        self._redraw()

    def set_loupe_px(self, diameter: int) -> None:
        self._loupe_px = clamp_loupe_px(diameter)
        self._redraw()

    def set_laser(self, on: bool) -> None:
        self._laser = bool(on)
        self._sync_cursor()
        self._redraw()

    def set_pan_mode(self, on: bool) -> None:
        self._pan_mode = bool(on)
        if not self._pan_mode:
            self._drag_from = None
        self._sync_cursor()

    def zoom_step(self, *, zoom_in: bool) -> None:
        self._scale = stepped_view_scale(self._scale, zoom_in=zoom_in)
        if self._scale <= 1.0:
            self._pan = QPoint(0, 0)
        self._redraw()

    @property
    def view_scale(self) -> float:
        return self._scale

    @property
    def loupe_px(self) -> int:
        return self._loupe_px

    def set_frame_pixmap(self, pix: QPixmap) -> None:
        self._source = pix
        self.setText("")
        self._redraw()

    def clear_frame(self) -> None:
        self._source = QPixmap()
        self._scale = 1.0
        self._pan = QPoint(0, 0)
        self._drag_from = None
        self.clear()
        self.setPixmap(QPixmap())
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._pan_mode:
            self._drag_from = event.position().toPoint()
            self._pan_from = QPoint(self._pan)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if self._drag_from is not None:
            delta = pos - self._drag_from
            self._pan = self._pan_from + delta
            self._redraw()
            return
        self._mouse = pos
        self._redraw()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_from = None
            self._sync_cursor()
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._mouse = QPoint(-1, -1)
        self._drag_from = None
        super().leaveEvent(event)
        self._sync_cursor()
        self._redraw()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        self._paint_contents(painter)

    def _paint_contents(self, painter: QPainter) -> None:
        box = self.contentsRect()
        dest = dest_rect(box, self._scale, self._pan)
        if not self._source.isNull() and not dest.isNull():
            painter.drawPixmap(dest, self._source)
        if self._mouse.x() < 0:
            return
        pix = self._source
        if self._loupe and not pix.isNull():
            paint_loupe(painter, pix, dest, self._mouse, diameter=self._loupe_px)
        if self._laser:
            paint_laser(painter, self._mouse)

    def _redraw(self) -> None:
        self.update()

    def _sync_cursor(self) -> None:
        if self._pan_mode:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            return
        if self._laser:
            self.setCursor(Qt.CursorShape.BlankCursor)
            return
        self.setCursor(Qt.CursorShape.ArrowCursor)


class OutputWindow(QMainWindow):
    hide_requested = Signal()

    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.setWindowTitle(OUTPUT_WINDOW_TITLE)
        self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
        self.setStyleSheet(DARK_QSS)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        self.canvas = OutputCanvas()
        grid.addWidget(self.canvas, 0, 0)
        self.btn_zoom_in = _chrome_button("＋")
        self.btn_zoom_out = _chrome_button("－")
        self.btn_pan = _chrome_button("✋", checkable=True)
        self.btn_loupe = _chrome_button("🔍", checkable=True)
        self.btn_laser = _chrome_button("⦿", checkable=True)
        self.slider_loupe = QSlider(Qt.Orientation.Horizontal)
        self.slider_loupe.setObjectName("outputLoupe")
        self.slider_loupe.setRange(MIN_LOUPE_PX, MAX_LOUPE_PX)
        self.slider_loupe.setValue(OUTPUT_LOUPE_PX)
        self.slider_loupe.setFixedWidth(128)
        self.slider_loupe.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.slider_loupe.setVisible(False)
        zoom = QFrame()
        zoom.setObjectName("outputChrome")
        zoom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        zoom_col = QVBoxLayout(zoom)
        zoom_col.setContentsMargins(0, 16, 16, 0)
        zoom_col.setSpacing(8)
        zoom_col.addWidget(self.btn_zoom_in)
        zoom_col.addWidget(self.btn_zoom_out)
        zoom_col.addWidget(self.btn_pan)
        tools = QFrame()
        tools.setObjectName("outputChrome")
        tools.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        tools_row = QHBoxLayout(tools)
        tools_row.setContentsMargins(0, 0, 16, 16)
        tools_row.setSpacing(8)
        tools_row.addWidget(self.btn_loupe)
        tools_row.addWidget(self.slider_loupe)
        tools_row.addWidget(self.btn_laser)
        self._zoom_chrome = zoom
        self._tools_chrome = tools
        grid.addWidget(zoom, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        grid.addWidget(tools, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        zoom.raise_()
        tools.raise_()
        self.setCentralWidget(host)
        self.btn_loupe.toggled.connect(self._on_loupe)
        self.btn_laser.toggled.connect(self.canvas.set_laser)
        self.btn_pan.toggled.connect(self.canvas.set_pan_mode)
        self.btn_zoom_in.clicked.connect(lambda: self.canvas.zoom_step(zoom_in=True))
        self.btn_zoom_out.clicked.connect(lambda: self.canvas.zoom_step(zoom_in=False))
        self.slider_loupe.valueChanged.connect(self.canvas.set_loupe_px)
        self.refresh()

    def set_loupe(self, on: bool) -> None:
        self.btn_loupe.setChecked(bool(on))

    def set_loupe_px(self, diameter: int) -> None:
        value = clamp_loupe_px(diameter)
        self.slider_loupe.blockSignals(True)
        self.slider_loupe.setValue(value)
        self.slider_loupe.blockSignals(False)
        self.canvas.set_loupe_px(value)

    def show_frame(self, bgr: np.ndarray) -> None:
        pix = bgr_to_pixmap(bgr)
        self.canvas.set_frame_pixmap(pix)
        self.present_canvas()

    def closeEvent(self, event) -> None:  # noqa: N802
        event.ignore()
        self.hide_requested.emit()

    def present_canvas(self) -> None:
        if not self.isVisible() or not self._gate.window_visible:
            return
        self.canvas.repaint()
        redraw_hwnd(int(self.winId()))

    def _on_loupe(self, on: bool) -> None:
        self.slider_loupe.setVisible(bool(on))
        self.canvas.set_loupe(on)

    def refresh(self) -> None:
        self.canvas.setText("")
        if self._gate.window_visible:
            self.setWindowTitle(OUTPUT_WINDOW_TITLE)
            self.setFixedSize(OUTPUT_WIDTH, OUTPUT_HEIGHT)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
            self.show()
            self.present_canvas()
            return
        self.canvas.clear_frame()
        self.setWindowTitle(IDLE_WINDOW_TITLE)
        self.hide()
