"""操作画面を OBS の画面取り込みから外す。配信用の窓には使わない。"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QWidget

_WDA_EXCLUDEFROMCAPTURE = 0x00000011


def exclude_from_capture(widget: QWidget) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(widget.winId())
        if hwnd:
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, _WDA_EXCLUDEFROMCAPTURE)
    except (AttributeError, OSError, ValueError):
        return
