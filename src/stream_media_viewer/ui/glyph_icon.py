"""ボタンの記号を大きな絵にする。文字は短い補助として下に置く。"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QToolButton

GLYPH_PX = 22
_SCALE = 3
_INK = "#f0f0f0"
_cache: dict[tuple[str, int, str], tuple[QIcon, QSize]] = {}


def glyph_icon(glyph: str, px: int = GLYPH_PX, color: str = _INK) -> tuple[QIcon, QSize]:
    """記号 1 つを描いた絵と、その表示の大きさ。横長の記号（あ/A）は横に広げる。"""
    key = (glyph, px, color)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    font = QFont()
    font.setPixelSize(int(px * 0.86) * _SCALE)
    metrics = QFontMetrics(font)
    width = max(px * _SCALE, metrics.horizontalAdvance(glyph) + 4 * _SCALE)
    pixmap = QPixmap(width, px * _SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(color))
    box = QRect(0, 0, pixmap.width(), pixmap.height())
    painter.drawText(box, Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()
    result = (QIcon(pixmap), QSize(width // _SCALE, px))
    _cache[key] = result
    return result


def set_glyph(button: QToolButton, glyph: str, text: str, tip: str) -> None:
    """記号を上の絵に、短い文字を下に。記号は property("glyph") で取り出せる。"""
    icon, size = glyph_icon(glyph)
    button.setIcon(icon)
    button.setIconSize(size)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    button.setText(text)
    button.setToolTip(tip)
    button.setProperty("glyph", glyph)
