from pathlib import Path

from stream_media_viewer.playback.preload import cache_key, estimate_item_bytes, format_bytes


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
    vivid = cache_key(path, **{**base, "enhance_level": "strong"})
    assert first != shifted
    assert first != marked
    assert first != vivid
    assert first == cache_key(path, **base)


def test_estimate_photos_are_small_videos_scale_with_time() -> None:
    photo = estimate_item_bytes("image", 0)
    minute = estimate_item_bytes("video", 60_000, 30.0)
    assert photo < 200_000
    assert minute > 50_000_000
    assert "MB" in format_bytes(minute) or "GB" in format_bytes(minute)
