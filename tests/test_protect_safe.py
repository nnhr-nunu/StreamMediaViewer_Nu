import numpy as np

from stream_media_viewer.detect.protect import protect_frame_safe


def test_protect_frame_safe_returns_none_on_empty_image() -> None:
    out, has_face, has_text = protect_frame_safe(
        np.zeros((0, 0, 3), dtype=np.uint8),
        face_blur=True,
        text_blur=True,
        marks=[],
        strength=25,
    )
    assert out is None
    assert has_face is False
    assert has_text is False


def test_protect_frame_safe_accepts_false_face_hashes() -> None:
    out, has_face, has_text = protect_frame_safe(
        np.zeros((32, 32, 3), dtype=np.uint8),
        face_blur=False,
        text_blur=False,
        marks=[],
        strength=25,
        false_face_hashes=["deadbeef"],
    )
    assert out is not None
    assert has_face is False
    assert has_text is False
