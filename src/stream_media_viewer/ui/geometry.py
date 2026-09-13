"""窓の位置を設定へ保存する。"""

from __future__ import annotations

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


def restore_saved_geometry(widget: QWidget, raw: str) -> bool:
    text = (raw or "").strip()
    if not text:
        return False
    xy = parse_xy_pos(text)
    if xy is not None:
        widget.move(xy[0], xy[1])
        return True
    try:
        data = bytes.fromhex(text)
    except ValueError:
        return False
    return bool(widget.restoreGeometry(data))
