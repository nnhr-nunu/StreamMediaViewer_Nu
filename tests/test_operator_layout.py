from PySide6.QtWidgets import QToolButton

from stream_media_viewer.safety.output_gate import OutputGate
from stream_media_viewer.ui.operator_window import OperatorWindow


def _bar_buttons(win: OperatorWindow) -> list[QToolButton]:
    bar = win._bar
    out = []
    for index in range(bar.count()):
        widget = bar.itemAt(index).widget()
        if isinstance(widget, QToolButton) and not widget.isHidden():
            out.append(widget)
    return out


def test_bottom_bar_goes_icon_only_instead_of_cutting_labels(qtbot) -> None:
    win = OperatorWindow(OutputGate())
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    win.set_false_face_visible(True)
    win.set_media_kind("video")
    win.resize(900, 560)
    qtbot.wait(80)
    for button in _bar_buttons(win):
        # 文字が「手...し」のように切れない
        assert button.width() >= button.sizeHint().width(), button.text()
    assert win.btn_manual.property("compact")
    assert not win.btn_send.property("compact")
    assert "送る" in win.btn_send.text()
    # 誤検出修正は名前を外しても ON／OFF は残す
    assert "OFF" in win.btn_false_face.text()
    assert "誤検出修正" not in win.btn_false_face.text()


def test_bottom_bar_keeps_captions_when_there_is_room(qtbot) -> None:
    win = OperatorWindow(OutputGate())
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    win.set_false_face_visible(True)
    win.set_media_kind("image")
    win.resize(1000, 700)
    qtbot.wait(80)
    assert not win.btn_manual.property("compact")
    assert "手動ぼかし" in win.btn_manual.text()
    assert "誤検出修正" in win.btn_false_face.text()
    for button in _bar_buttons(win):
        assert button.width() >= button.sizeHint().width(), button.text()


def test_preview_can_shrink_so_the_small_window_does_not_cut_it(qtbot) -> None:
    win = OperatorWindow(OutputGate())
    qtbot.addWidget(win)
    # 最小の窓（900×560）で動画の区間の棒まで出しても、確認画面が枠からはみ出さない
    assert win.preview.minimumHeight() <= 100
    assert win.preview.minimumWidth() <= 520
