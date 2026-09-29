from stream_media_viewer.ui.geometry import parse_xy_pos, restore_saved_geometry


def test_parse_xy_pos_reads_comma_pair() -> None:
    assert parse_xy_pos("80,120") == (80, 120)
    assert parse_xy_pos("  -10 , 30 ") == (-10, 30)


def test_parse_xy_pos_rejects_geometry_hex() -> None:
    assert parse_xy_pos("01020304aabb") is None
    assert parse_xy_pos("") is None
    assert parse_xy_pos("80") is None


def test_restore_xy_moves_widget(qtbot) -> None:
    from PySide6.QtWidgets import QWidget

    widget = QWidget()
    qtbot.addWidget(widget)
    assert restore_saved_geometry(widget, "40,50")
    assert (widget.x(), widget.y()) == (40, 50)


def test_output_position_is_restored_even_partly_off_screen(qtbot) -> None:
    # 配信用の窓は画面の外に一部はみ出して置いてよい。次の起動で画面内へ引き戻さない。
    from PySide6.QtGui import QGuiApplication

    from stream_media_viewer.safety.output_gate import OutputGate
    from stream_media_viewer.ui.geometry import window_pos_text
    from stream_media_viewer.ui.output_window import OutputWindow

    screen = QGuiApplication.primaryScreen().geometry()
    first = OutputWindow(OutputGate())
    qtbot.addWidget(first)
    first.move(screen.x() - 300, screen.y() + 40)
    saved = window_pos_text(first)
    second = OutputWindow(OutputGate())
    qtbot.addWidget(second)
    assert restore_saved_geometry(second, saved)
    assert (second.x(), second.y()) == (screen.x() - 300, screen.y() + 40)


def test_position_on_a_removed_screen_is_not_restored(qtbot) -> None:
    # 2 枚目の画面を外したあとなど、どの画面にも掛からない位置へは戻さない（見失わない）
    from PySide6.QtWidgets import QWidget

    widget = QWidget()
    qtbot.addWidget(widget)
    widget.move(10, 10)
    assert not restore_saved_geometry(widget, "100000,100000")
    assert (widget.x(), widget.y()) == (10, 10)
    # 壊れた値でも落ちない
    assert not restore_saved_geometry(widget, "zz-not-hex")
