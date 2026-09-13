from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel

from stream_media_viewer.detect.blur import DEFAULT_BRUSH_WIDTH
from stream_media_viewer.ui.overlays import OPERATOR_LOUPE_PX, paint_loupe

_CLICK_PX = 8


class PreviewCanvas(QLabel):
    mark_added = Signal(dict)
    clicked = Signal()
    region_clicked = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("preview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(560, 315)
        self.setContentsMargins(0, 0, 0, 0)
        self.mode = "off"
        self.click_toggles_play = False
        self.brush_width = DEFAULT_BRUSH_WIDTH
        self._origin: QPoint | None = None
        self._current: QRect | None = None
        self._stroke: list[tuple[float, float]] = []
        self._pixmap: QPixmap | None = None
        self._fit_timer = QTimer(self)
        self._fit_timer.setSingleShot(True)
        self._fit_timer.timeout.connect(self._refit)
        self._loupe = False
        self._mouse = QPoint(-1, -1)
        self.setMouseTracking(True)

    def set_frame(self, pixmap: QPixmap, *, smooth: bool = True) -> None:
        self._pixmap = pixmap
        transform = (
            Qt.TransformationMode.SmoothTransformation
            if smooth
            else Qt.TransformationMode.FastTransformation
        )
        box = self.contentsRect().size()
        self.setPixmap(
            pixmap.scaled(
                box if box.width() > 1 else self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                transform,
            )
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._fit_timer.start(60)

    def set_loupe(self, on: bool) -> None:
        self._loupe = bool(on)
        self.update()

    def _refit(self) -> None:
        if self._pixmap:
            self.set_frame(self._pixmap)

    def _content_rect(self) -> QRect:
        pix = self.pixmap()
        if pix is None or pix.isNull():
            return QRect()
        cr = self.contentsRect()
        dpr = float(pix.devicePixelRatio() or 1.0)
        pw = pix.width() / dpr
        ph = pix.height() / dpr
        x = cr.x() + int((cr.width() - pw) / 2)
        y = cr.y() + int((cr.height() - ph) / 2)
        return QRect(x, y, max(1, int(pw)), max(1, int(ph)))

    def _norm(self, pos: QPoint) -> tuple[float, float] | None:
        box = self._content_rect()
        if box.isNull() or not box.contains(pos):
            return None
        return ((pos.x() - box.x()) / box.width(), (pos.y() - box.y()) / box.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._origin = event.position().toPoint()
        if self.mode == "stroke":
            pt = self._norm(self._origin)
            self._stroke = [pt] if pt else []

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if self._loupe:
            self._mouse = pos
            self.update()
        if self._origin is None:
            return
        if self.mode == "rect":
            self._current = QRect(self._origin, pos).normalized()
            self.update()
        elif self.mode == "stroke":
            pt = self._norm(pos)
            if pt:
                self._stroke.append(pt)
                self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._mouse = QPoint(-1, -1)
        super().leaveEvent(event)
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
        if click and self.mode == "off":
            pt = self._norm(origin)
            self._origin = None
            self._current = None
            self._stroke = []
            self.update()
            if pt is not None:
                self.region_clicked.emit(pt[0], pt[1])
            elif self.click_toggles_play:
                self.clicked.emit()
            return
        if click and self.click_toggles_play:
            self._origin = None
            self._current = None
            self._stroke = []
            self.update()
            self.clicked.emit()
            return
        box = self._content_rect()
        if self.mode == "rect" and self._current and box.width() > 0 and box.height() > 0:
            nx = (self._current.x() - box.x()) / box.width()
            ny = (self._current.y() - box.y()) / box.height()
            nw = self._current.width() / box.width()
            nh = self._current.height() / box.height()
            if nw > 0.01 and nh > 0.01:
                self.mark_added.emit({"kind": "rect", "x": nx, "y": ny, "w": nw, "h": nh})
        elif self.mode == "stroke" and len(self._stroke) >= 2:
            pix_w = max(1, box.width())
            self.mark_added.emit(
                {
                    "kind": "stroke",
                    "points": self._stroke,
                    "width": self.brush_width / pix_w,
                }
            )
        self._origin = None
        self._current = None
        self._stroke = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        box = self._content_rect()
        painter.setPen(QPen(Qt.GlobalColor.magenta, 2))
        if self._current:
            painter.drawRect(self._current)
        if len(self._stroke) >= 2 and box.width() > 0:
            pts = []
            painter.setPen(
                QPen(
                    Qt.GlobalColor.magenta,
                    max(1, self.brush_width),
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            for x, y in self._stroke:
                pts.append(QPoint(int(box.x() + x * box.width()), int(box.y() + y * box.height())))
            for a, b in zip(pts, pts[1:], strict=False):
                painter.drawLine(a, b)
        if self._loupe and self._pixmap is not None and not self._pixmap.isNull():
            paint_loupe(painter, self._pixmap, box, self._mouse, diameter=OPERATOR_LOUPE_PX)
