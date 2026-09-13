import numpy as np

from stream_media_viewer.detect.blur import Box, gaussian_oval, gaussian_region


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
