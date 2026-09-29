from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.ui.drop_hint import CalendarDateEdit
from stream_media_viewer.ui.operator_window import OperatorWindow


def _key(key: Qt.Key, modifiers=Qt.KeyboardModifier.KeypadModifier) -> QKeyEvent:
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers)


def test_date_edit_never_takes_the_keys(qtbot) -> None:
    # カレンダーで選んだあと日付欄がキーを吸うと、テンキーの 0（緊急）が効かなくなる。
    date = CalendarDateEdit()
    qtbot.addWidget(date)
    assert date.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert date.lineEdit().focusPolicy() == Qt.FocusPolicy.NoFocus
    for target in (date, date.lineEdit()):
        override = QKeyEvent(
            QEvent.Type.ShortcutOverride, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier
        )
        QApplication.sendEvent(target, override)
        assert not override.isAccepted()


def test_numpad_keys_that_reach_the_window_still_work(qtbot) -> None:
    win = OperatorWindow(OutputGate())
    qtbot.addWidget(win)
    hits: list[str] = []
    win.panic_requested.connect(lambda: hits.append("panic"))
    win.next_requested.connect(lambda: hits.append("next"))
    win.prev_requested.connect(lambda: hits.append("prev"))
    win.play_requested.connect(lambda: hits.append("play"))
    win.send_requested.connect(lambda: hits.append("send"))
    for key in (Qt.Key.Key_0, Qt.Key.Key_6, Qt.Key.Key_4, Qt.Key.Key_5, Qt.Key.Key_Enter):
        QApplication.sendEvent(win, _key(key))
    QApplication.sendEvent(win, _key(Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert hits == ["panic", "next", "prev", "play", "send", "panic"]


def test_modified_keys_are_not_taken_by_the_fallback(qtbot) -> None:
    win = OperatorWindow(OutputGate())
    qtbot.addWidget(win)
    hits: list[str] = []
    win.panic_requested.connect(lambda: hits.append("panic"))
    QApplication.sendEvent(win, _key(Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier))
    assert hits == []
