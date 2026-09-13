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
