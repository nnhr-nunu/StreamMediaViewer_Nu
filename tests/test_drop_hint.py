import sys

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QAbstractSpinBox

from stream_media_viewer.ui.drop_hint import CalendarDateEdit, DropHintCombo, arrow_rect


def test_arrow_rect_stays_inside_combo(qtbot) -> None:
    combo = DropHintCombo()
    combo.addItem("京都")
    qtbot.addWidget(combo)
    combo.resize(160, 36)
    combo.show()
    qtbot.waitExposed(combo)
    inner = combo.rect().adjusted(3, 1, -3, -1)
    assert inner.contains(arrow_rect(combo))


def test_arrow_rect_stays_inside_date(qtbot) -> None:
    date = CalendarDateEdit()
    qtbot.addWidget(date)
    date.resize(124, 36)
    date.show()
    qtbot.waitExposed(date)
    inner = date.rect().adjusted(3, 1, -3, -1)
    assert inner.contains(arrow_rect(date))
    assert date.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons


@pytest.mark.skipif(sys.platform == "darwin", reason="GitHub Mac runner ではカレンダー弹出を安定して確認できない")
def test_date_edit_opens_calendar_from_text_area(qtbot) -> None:
    date = CalendarDateEdit()
    qtbot.addWidget(date)
    date.show()
    qtbot.waitExposed(date)
    qtbot.mouseClick(date, Qt.MouseButton.LeftButton, pos=QPoint(16, date.height() // 2))
    calendar = date.calendarWidget()
    assert calendar is not None
    qtbot.waitUntil(calendar.isVisible, timeout=1000)
