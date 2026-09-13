"""フォルダ・場所・日付がプルダウンだと分かる印。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QCalendarWidget, QComboBox, QDateEdit

_HINT = "▼"


def _paint_hint(widget, painter: QPainter) -> None:
    painter.setPen(widget.palette().color(widget.foregroundRole()))
    arrow = widget.rect().adjusted(widget.width() - 26, 0, -4, 0)
    painter.drawText(arrow, Qt.AlignmentFlag.AlignCenter, _HINT)


class DropHintCombo(QComboBox):
    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        _paint_hint(self, painter)


class CalendarDateEdit(QDateEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy/MM/dd")
        calendar = QCalendarWidget(self)
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setCalendarWidget(calendar)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        _paint_hint(self, painter)
