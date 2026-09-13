import numpy as np

from stream_media_viewer.render.enhance import enhance_bgr


def test_enhance_off_leaves_pixels_unchanged() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    out = enhance_bgr(frame, enabled=False)
    assert np.array_equal(out, frame)


def test_enhance_on_does_not_rewrite_source() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    original = frame.copy()
    enhance_bgr(frame, enabled=True)
    assert np.array_equal(frame, original)


def test_enhance_on_changes_a_colored_frame() -> None:
    frame = np.full((8, 8, 3), (30, 80, 200), dtype=np.uint8)
    out = enhance_bgr(frame, enabled=True)
    assert not np.array_equal(out, frame)
