from pathlib import Path

from stream_media_viewer.playback.preload import cache_key


def test_cache_key_changes_when_marks_or_range_change(tmp_path: Path) -> None:
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"fake")
    base = dict(
        in_ms=0,
        out_ms=1000,
        face_blur=True,
        text_blur=False,
        strength=25,
        marks=[],
    )
    first = cache_key(path, **base)
    shifted = cache_key(path, **{**base, "in_ms": 200})
    marked = cache_key(path, **{**base, "marks": [{"kind": "rect", "x": 0.1}]})
    assert first != shifted
    assert first != marked
    assert first == cache_key(path, **base)
