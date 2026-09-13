import numpy as np

from stream_media_viewer.detect.protect import protect_for_note
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.render.rotate import clamp_rotation, rotate_bgr, rotate_marks
from stream_media_viewer.settings import AppSettings


def test_clamp_rotation_keeps_right_angles() -> None:
    assert clamp_rotation(90) == 90
    assert clamp_rotation(360) == 0
    assert clamp_rotation("270") == 270
    assert clamp_rotation(45) == 0
    assert clamp_rotation("nope") == 0


def test_rotate_bgr_clockwise_swaps_sides() -> None:
    bgr = np.zeros((10, 20, 3), dtype=np.uint8)
    bgr[0, 0] = (0, 0, 255)
    turned = rotate_bgr(bgr, 90)
    assert turned.shape[:2] == (20, 10)
    assert tuple(turned[0, 9]) == (0, 0, 255)


def test_rotate_marks_rect_clockwise() -> None:
    marks = [{"kind": "rect", "x": 0.0, "y": 0.0, "w": 0.5, "h": 0.25}]
    turned = rotate_marks(marks, 90)
    assert turned[0]["x"] == 0.75
    assert turned[0]["y"] == 0.0
    assert turned[0]["w"] == 0.25
    assert turned[0]["h"] == 0.5


def test_protect_for_note_applies_rotation() -> None:
    bgr = np.zeros((10, 20, 3), dtype=np.uint8)
    settings = AppSettings(face_blur=False, text_blur=False)
    out, _, _ = protect_for_note(bgr, settings, FileNote(rotation=90))
    assert out is not None
    assert out.shape[:2] == (20, 10)
