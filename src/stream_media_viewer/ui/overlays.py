"""確認プレビューと配信用の窓に重ねる拡大とレーザー。文字は出さない。"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPixmap, QRadialGradient

LOUPE_ZOOM = 2.4
MIN_LOUPE_PX = 80
MAX_LOUPE_PX = 480
OPERATOR_LOUPE_PX = 168
OUTPUT_LOUPE_PX = 260
LASER_RADIUS = 22


def clamp_loupe_px(raw: object) -> int:
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return OPERATOR_LOUPE_PX
    return max(MIN_LOUPE_PX, min(MAX_LOUPE_PX, value))


def paint_loupe(
    painter: QPainter,
    source: QPixmap,
    content: QRect,
    mouse: QPoint,
    *,
    diameter: int,
) -> None:
    if source.isNull() or content.isNull() or not content.contains(mouse):
        return
    nx = (mouse.x() - content.x()) / content.width()
    ny = (mouse.y() - content.y()) / content.height()
    src_w = max(1, int(diameter / LOUPE_ZOOM * source.width() / max(1, content.width())))
    src_h = max(1, int(diameter / LOUPE_ZOOM * source.height() / max(1, content.height())))
    cx = int(nx * source.width())
    cy = int(ny * source.height())
    sx = max(0, min(source.width() - src_w, cx - src_w // 2))
    sy = max(0, min(source.height() - src_h, cy - src_h // 2))
    patch = source.copy(sx, sy, min(src_w, source.width()), min(src_h, source.height()))
    if patch.isNull():
        return
    dest = QRect(mouse.x() - diameter // 2, mouse.y() - diameter // 2, diameter, diameter)
    scaled = patch.scaled(
        dest.size(),
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.FastTransformation,
    )
    clip = QPainterPath()
    clip.addEllipse(dest)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setClipPath(clip)
    painter.drawPixmap(dest, scaled)
    painter.setClipping(False)
    painter.setPen(QColor(220, 220, 220, 220))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(dest)
    painter.restore()


def paint_laser(painter: QPainter, pos: QPoint, *, radius: int = LASER_RADIUS) -> None:
    gradient = QRadialGradient(pos, radius)
    gradient.setColorAt(0.0, QColor(255, 80, 80, 230))
    gradient.setColorAt(0.35, QColor(255, 40, 40, 160))
    gradient.setColorAt(1.0, QColor(255, 0, 0, 0))
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(pos, radius, radius)
    painter.restore()
