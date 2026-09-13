from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel

_CLICK_PX = 8


class PreviewCanvas(QLabel):
    mark_added = Signal(dict)
    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("preview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 270)
        self.mode = "rect"
        self.click_toggles_play = False
        self._origin: QPoint | None = None
        self._current: QRect | None = None
        self._stroke: list[tuple[float, float]] = []
        self._pixmap: QPixmap | None = None

    def set_frame(self, pixmap: QPixmap, *, smooth: bool = True) -> None:
        self._pixmap = pixmap
        transform = (
            Qt.TransformationMode.SmoothTransformation
            if smooth
            else Qt.TransformationMode.FastTransformation
        )
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                transform,
            )
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._pixmap:
            self.set_frame(self._pixmap)

    def _norm(self, pos: QPoint) -> tuple[float, float] | None:
        pix = self.pixmap()
        if pix is None or pix.isNull():
            return None
        x0 = (self.width() - pix.width()) // 2
        y0 = (self.height() - pix.height()) // 2
        if not QRect(x0, y0, pix.width(), pix.height()).contains(pos):
            return None
        return ((pos.x() - x0) / pix.width(), (pos.y() - y0) / pix.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._origin = event.position().toPoint()
        if self.mode == "stroke":
            pt = self._norm(self._origin)
            self._stroke = [pt] if pt else []

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._origin is None:
            return
        pos = event.position().toPoint()
        if self.mode == "rect":
            self._current = QRect(self._origin, pos).normalized()
            self.update()
        else:
            pt = self._norm(pos)
            if pt:
                self._stroke.append(pt)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pix = self.pixmap()
        origin = self._origin
        if pix is None or origin is None:
            self._origin = None
            return
        pos = event.position().toPoint()
        click = abs(pos.x() - origin.x()) < _CLICK_PX and abs(pos.y() - origin.y()) < _CLICK_PX
        if click and self.click_toggles_play:
            self._origin = None
            self._current = None
            self._stroke = []
            self.update()
            self.clicked.emit()
            return
        x0 = (self.width() - pix.width()) // 2
        y0 = (self.height() - pix.height()) // 2
        if self.mode == "rect" and self._current:
            nx = (self._current.x() - x0) / pix.width()
            ny = (self._current.y() - y0) / pix.height()
            nw = self._current.width() / pix.width()
            nh = self._current.height() / pix.height()
            if nw > 0.01 and nh > 0.01:
                self.mark_added.emit({"kind": "rect", "x": nx, "y": ny, "w": nw, "h": nh})
        elif self.mode == "stroke" and len(self._stroke) >= 2:
            self.mark_added.emit({"kind": "stroke", "points": self._stroke})
        self._origin = None
        self._current = None
        self._stroke = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.magenta, 2))
        if self._current:
            painter.drawRect(self._current)
        if len(self._stroke) >= 2:
            pts = []
            pix = self.pixmap()
            if pix:
                x0 = (self.width() - pix.width()) // 2
                y0 = (self.height() - pix.height()) // 2
                for x, y in self._stroke:
                    pts.append(QPoint(int(x0 + x * pix.width()), int(y0 + y * pix.height())))
                for a, b in zip(pts, pts[1:], strict=False):
                    painter.drawLine(a, b)
