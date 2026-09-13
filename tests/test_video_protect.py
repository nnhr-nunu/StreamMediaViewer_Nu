import numpy as np

from stream_media_viewer.playback.video import VideoPlayer


def test_protect_error_keeps_last_safe_frame_not_raw(qtbot) -> None:
    player = VideoPlayer()
    safe = np.full((4, 4, 3), 40, dtype=np.uint8)
    raw = np.full((4, 4, 3), 200, dtype=np.uint8)
    player._last_ok = safe

    def boom(_frame: np.ndarray) -> np.ndarray:
        raise RuntimeError("detect failed")

    player.set_protect(boom)
    out = player._apply(raw)
    assert out is not None
    assert np.array_equal(out, safe)
    assert not np.array_equal(out, raw)
    player.close()
    assert player._last_ok is None
