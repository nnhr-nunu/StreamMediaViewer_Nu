"""窓の位置を設定へ保存する。"""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def parse_xy_pos(raw: str) -> tuple[int, int] | None:
    text = (raw or "").strip()
    if "," not in text:
        return None
    left, right = text.split(",", 1)
    try:
        return int(left.strip()), int(right.strip())
    except ValueError:
        return None


def geometry_hex(widget: QWidget) -> str:
    return widget.saveGeometry().toHex().data().decode("ascii")


def window_pos_text(widget: QWidget) -> str:
    """窓の左上（枠を含む）を "x,y" で。配信用の窓は画面の外に一部はみ出していてもよい。"""
    pos = widget.pos()
    return f"{pos.x()},{pos.y()}"


def _touches_a_screen(widget: QWidget, x: int, y: int) -> bool:
    screens = QGuiApplication.screens()
    if not screens:
        return True
    frame = widget.frameGeometry()
    rect = QRect(x, y, max(1, frame.width()), max(1, frame.height()))
    return any(screen.geometry().intersects(rect) for screen in screens)


def restore_saved_geometry(widget: QWidget, raw: str) -> bool:
    """保存した位置へ戻す。"x,y" はそのまま戻す（画面へ引き戻さない）。

    ただし 2 枚目の画面を外したなどで、どの画面にも掛からないときは戻さない（見失わないように）。
    """
    text = (raw or "").strip()
    if not text:
        return False
    xy = parse_xy_pos(text)
    if xy is not None:
        if not _touches_a_screen(widget, xy[0], xy[1]):
            return False
        widget.move(xy[0], xy[1])
        return True
    try:
        data = bytes.fromhex(text)
    except ValueError:
        return False
    return bool(widget.restoreGeometry(data))
