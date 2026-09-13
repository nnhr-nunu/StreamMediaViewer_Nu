import numpy as np

from stream_media_viewer.detect.blur import Box, apply_marks, gaussian_oval, gaussian_region


def test_gaussian_oval_leaves_box_corners_closer_to_original() -> None:
    bgr = np.zeros((80, 80, 3), dtype=np.uint8)
    bgr[:] = 30
    bgr[28:52, 28:52] = 220
    oval = bgr.copy()
    rect = bgr.copy()
    box = Box(10, 10, 60, 60)
    gaussian_oval(oval, box, 81)
    gaussian_region(rect, box, 81)
    oval_corner = abs(int(oval[12, 12, 0]) - 30)
    rect_corner = abs(int(rect[12, 12, 0]) - 30)
    oval_center = abs(int(oval[40, 40, 0]) - 220)
    assert oval_corner < rect_corner
    assert oval_center > 0
    assert oval_corner < 20


def test_stroke_blur_stays_near_the_path() -> None:
    h, w = 80, 200
    bgr = np.full((h, w, 3), 40, dtype=np.uint8)
    bgr[38:43, :] = 200
    original = bgr.copy()
    apply_marks(
        bgr,
        [{"kind": "stroke", "points": [(0.2, 0.5), (0.8, 0.5)], "width": 0.04}],
        31,
    )
    assert np.array_equal(bgr[0], original[0])
    assert np.array_equal(bgr[h - 1], original[h - 1])
    assert not np.array_equal(bgr[40, 100], original[40, 100])



def test_gaussian_oval_leaves_box_corners_closer_to_original() -> None:
    bgr = np.zeros((80, 80, 3), dtype=np.uint8)
    bgr[:] = 30
    bgr[28:52, 28:52] = 220
    oval = bgr.copy()
    rect = bgr.copy()
    box = Box(10, 10, 60, 60)
    gaussian_oval(oval, box, 81)
    gaussian_region(rect, box, 81)
    oval_corner = abs(int(oval[12, 12, 0]) - 30)
    rect_corner = abs(int(rect[12, 12, 0]) - 30)
    oval_center = abs(int(oval[40, 40, 0]) - 220)
    assert oval_corner < rect_corner
    assert oval_center > 0
    assert oval_corner < 20
