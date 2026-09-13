"""配信用の窓の全体ズームと移動。はみ出しは許容する。"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect

MIN_VIEW_SCALE = 1.0
MAX_VIEW_SCALE = 8.0
VIEW_SCALE_STEP = 1.25


def clamp_view_scale(raw: float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return MIN_VIEW_SCALE
    return max(MIN_VIEW_SCALE, min(MAX_VIEW_SCALE, value))


def stepped_view_scale(current: float, *, zoom_in: bool) -> float:
    scale = clamp_view_scale(current)
    if zoom_in:
        return clamp_view_scale(scale * VIEW_SCALE_STEP)
    return clamp_view_scale(scale / VIEW_SCALE_STEP)


def dest_rect(view: QRect, scale: float, pan: QPoint) -> QRect:
    if view.isNull() or view.width() < 1 or view.height() < 1:
        return QRect()
    factor = clamp_view_scale(scale)
    width = max(1, int(round(view.width() * factor)))
    height = max(1, int(round(view.height() * factor)))
    x = view.x() + (view.width() - width) // 2 + pan.x()
    y = view.y() + (view.height() - height) // 2 + pan.y()
    return QRect(x, y, width, height)
