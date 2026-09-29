import numpy as np

from stream_media_viewer.detect.blur import (
    Box,
    apply_marks,
    gaussian_oval,
    gaussian_region,
    oval_tilt,
)


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


def test_gaussian_oval_angle_blurs_box_corners_more() -> None:
    bgr = np.full((80, 80, 3), 30, dtype=np.uint8)
    bgr[32:48, 22:58] = 220
    aligned = bgr.copy()
    rotated = bgr.copy()
    gaussian_oval(aligned, Box(10, 25, 60, 30), 81)
    gaussian_oval(rotated, Box(10, 25, 60, 30, angle=45.0), 81)
    aligned_shift = abs(int(aligned[25, 17, 0]) - 30)
    rotated_shift = abs(int(rotated[25, 17, 0]) - 30)
    assert rotated_shift > aligned_shift
    assert rotated_shift > 0


def test_rect_starting_outside_the_image_still_blurs_the_inside() -> None:
    bgr = np.zeros((60, 60, 3), dtype=np.uint8)
    bgr[:, ::2] = 255
    original = bgr.copy()
    # 黒帯から引き始めた四角（x が負）。末尾から数えるスライスで空振りしないこと。
    apply_marks(bgr, [{"kind": "rect", "x": -0.1, "y": 0.2, "w": 0.5, "h": 0.5}], 31)
    assert not np.array_equal(bgr[30, 5:20], original[30, 5:20])
    assert np.array_equal(bgr[30, 40:], original[30, 40:])


def test_box_with_negative_size_blurs_the_same_area() -> None:
    bgr = np.zeros((40, 40, 3), dtype=np.uint8)
    bgr[:, ::2] = 255
    forward = bgr.copy()
    backward = bgr.copy()
    gaussian_region(forward, Box(5, 5, 20, 20), 31)
    gaussian_region(backward, Box(25, 25, -20, -20), 31)
    assert np.array_equal(forward, backward)
    assert not np.array_equal(forward, bgr)


def test_max_blur_strength_on_tiny_roi_does_not_raise() -> None:
    bgr = np.zeros((8, 8, 3), dtype=np.uint8)
    gaussian_region(bgr, Box(0, 0, 8, 8), 300)
    gaussian_oval(bgr, Box(0, 0, 8, 8), 300)
    gaussian_region(bgr, Box(1, 1, 2, 2), 300)
    apply_marks(
        bgr,
        [{"kind": "rect", "x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}],
        300,
    )


def test_oval_tilt_keeps_small_tilts_and_folds_sideways_ones() -> None:
    assert oval_tilt(0.0) == 0.0
    assert oval_tilt(30.0) == 30.0
    assert oval_tilt(-45.0) == -45.0
    assert oval_tilt(45.0) == 45.0
    assert oval_tilt(90.0) == 0.0
    assert oval_tilt(-90.0) == 0.0
    assert oval_tilt(60.0) == -30.0
    assert oval_tilt(180.0) == 0.0
    assert oval_tilt(float("nan")) == 0.0


def test_gaussian_oval_sideways_face_blurs_both_ends_of_a_wide_box() -> None:
    # 横倒しの顔（目の線が縦 = 90°）の枠は横長。楕円が縦長になって左右の端が残らないこと。
    bgr = np.zeros((100, 200, 3), dtype=np.uint8)
    bgr[:, ::2] = 255
    upright = bgr.copy()
    sideways = bgr.copy()
    gaussian_oval(upright, Box(0, 0, 200, 100), 41)
    gaussian_oval(sideways, Box(0, 0, 200, 100, angle=90.0), 41)
    assert not np.array_equal(sideways[50, 20:40], bgr[50, 20:40])
    assert not np.array_equal(sideways[50, 160:180], bgr[50, 160:180])
    assert np.array_equal(sideways, upright)
