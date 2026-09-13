import numpy as np

from stream_media_viewer.render.enhance import (
    enhance_bgr,
    next_enhance_level,
    parse_enhance_level,
)


def test_parse_enhance_level_keeps_old_true_as_weak() -> None:
    assert parse_enhance_level(True) == "weak"
    assert parse_enhance_level(False) == "off"
    assert parse_enhance_level("strong") == "strong"


def test_next_enhance_level_cycles_off_weak_strong() -> None:
    assert next_enhance_level("off") == "weak"
    assert next_enhance_level("weak") == "strong"
    assert next_enhance_level("strong") == "off"


def test_enhance_off_leaves_pixels_unchanged() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    out = enhance_bgr(frame, level="off")
    assert np.array_equal(out, frame)


def test_enhance_does_not_rewrite_source() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    original = frame.copy()
    enhance_bgr(frame, level="strong")
    assert np.array_equal(frame, original)


def test_strong_moves_pixels_farther_than_weak() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    weak = enhance_bgr(frame, level="weak")
    strong = enhance_bgr(frame, level="strong")
    weak_delta = np.abs(weak.astype(np.int16) - frame.astype(np.int16)).sum()
    strong_delta = np.abs(strong.astype(np.int16) - frame.astype(np.int16)).sum()
    assert weak_delta > 0
    assert strong_delta > weak_delta
