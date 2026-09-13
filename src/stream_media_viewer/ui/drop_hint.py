"""フォルダ・場所・日付がプルダウンだと分かる印。"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, QRect, Qt
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QAbstractSpinBox, QCalendarWidget, QComboBox, QDateEdit

_HINT = "▼"
_ARROW_INSET = 4
_ARROW_WIDTH = 20


def arrow_rect(widget) -> QRect:
    """▼ を描く位置。枠の内側に収める。"""
    box = widget.rect().adjusted(_ARROW_INSET, 2, -_ARROW_INSET, -2)
    if box.width() < 8 or box.height() < 8:
        return widget.rect()
    width = min(_ARROW_WIDTH, max(16, box.width() // 5))
    return QRect(box.right() - width + 1, box.top(), width, box.height())


def _paint_hint(widget, painter: QPainter) -> None:
    painter.setPen(widget.palette().color(widget.foregroundRole()))
    font = painter.font()
    font.setPixelSize(11)
    painter.setFont(font)
    painter.drawText(arrow_rect(widget), Qt.AlignmentFlag.AlignCenter, _HINT)


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
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        calendar = QCalendarWidget(self)
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setCalendarWidget(calendar)
        edit = self.lineEdit()
        if edit is not None:
            edit.setReadOnly(True)
            edit.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self.lineEdit() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._open_calendar()
                return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_calendar()
            return
        super().mousePressEvent(event)

    def _open_calendar(self) -> None:
        hit = arrow_rect(self).center()
        press = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(hit),
            QPointF(self.mapToGlobal(hit)),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        super().mousePressEvent(press)
