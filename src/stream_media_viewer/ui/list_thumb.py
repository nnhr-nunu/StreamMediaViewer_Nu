"""一覧縮小画の印。配信用の窓には出さない。"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygon

_BADGE = 36


def with_video_mark(pixmap: QPixmap | None, size: int) -> QPixmap:
    if pixmap is None or pixmap.isNull():
        canvas = QPixmap(size, size)
        canvas.fill(QColor("#1b1b1b"))
    else:
        canvas = pixmap.copy()
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    margin = 8
    box = QRect(margin, canvas.height() - margin - _BADGE, _BADGE, _BADGE)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, 180))
    painter.drawEllipse(box)
    painter.setBrush(QColor("#f0f0f0"))
    cx, cy = box.center().x(), box.center().y()
    triangle = QPolygon(
        [
            QPoint(cx - 6, cy - 8),
            QPoint(cx - 6, cy + 8),
            QPoint(cx + 9, cy),
        ]
    )
    painter.drawPolygon(triangle)
    painter.setPen(QPen(QColor("#c9a0ff"), 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(box)
    painter.end()
    return canvas
