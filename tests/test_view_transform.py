from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPixmap

from stream_media_viewer.ui.overlays import clamp_loupe_px
from stream_media_viewer.ui.view_transform import dest_rect, stepped_view_scale
from stream_media_viewer.ui.win_present import present_opaque_pixmap


def test_dest_rect_grows_from_center() -> None:
    view = QRect(0, 0, 200, 100)
    box = dest_rect(view, 2.0, QPoint(0, 0))
    assert box.size().width() == 400
    assert box.size().height() == 200
    assert box.x() == -100
    assert box.y() == -50


def test_dest_rect_applies_pan() -> None:
    view = QRect(0, 0, 100, 100)
    box = dest_rect(view, 1.0, QPoint(12, -8))
    assert box.topLeft() == QPoint(12, -8)


def test_stepped_scale_stays_in_range() -> None:
    assert stepped_view_scale(1.0, zoom_in=False) == 1.0
    bigger = stepped_view_scale(1.0, zoom_in=True)
    assert bigger > 1.0
    assert stepped_view_scale(99.0, zoom_in=True) <= 8.0


def test_clamp_loupe_px() -> None:
    assert clamp_loupe_px(10) == 80
    assert clamp_loupe_px(999) == 480
    assert clamp_loupe_px("nope") == 168


def test_present_skips_invalid_handle(qtbot) -> None:
    from PySide6.QtCore import Qt

    pix = QPixmap(8, 8)
    pix.fill(Qt.GlobalColor.black)
    assert present_opaque_pixmap(0, pix) is False
    assert present_opaque_pixmap(1, QPixmap()) is False
