from pathlib import Path

import numpy as np

from stream_media_viewer.playback.preload import (
    cache_is_ready,
    cache_key,
    estimate_item_bytes,
    format_bytes,
    read_protected_image,
    write_protected_image,
)


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
    skipped = cache_key(path, **{**base, "skip_faces": True})
    assert first != skipped
    rotated = cache_key(path, **{**base, "rotation": 90})
    assert first != rotated
    legacy = cache_key(path, **{**base, "face_pipeline": "legacy"})
    assert first != legacy
    assert first == cache_key(path, **base)


def test_estimate_photos_are_small_videos_scale_with_time() -> None:
    photo = estimate_item_bytes("image", 0)
    minute = estimate_item_bytes("video", 60_000, 30.0)
    assert photo < 200_000
    assert minute > 50_000_000
    assert "MB" in format_bytes(minute) or "GB" in format_bytes(minute)


def test_write_protected_image_round_trips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "stream_media_viewer.playback.preload.preload_root", lambda: tmp_path / "preload"
    )
    frame = np.full((24, 32, 3), 40, dtype=np.uint8)
    assert write_protected_image("folder", "photoA", frame, has_face=True, has_text=False)
    assert cache_is_ready("photoA", "folder")
    loaded = read_protected_image("folder", "photoA")
    assert loaded is not None
    bgr, faces, texts = loaded
    assert bgr.shape[0] == 24
    assert bgr.shape[1] == 32
    assert faces is True
    assert texts is False


def test_write_protected_image_keeps_aspect_without_letterbox(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "stream_media_viewer.playback.preload.preload_root", lambda: tmp_path / "preload"
    )
    tall = np.full((4000, 1000, 3), 80, dtype=np.uint8)
    assert write_protected_image("folder", "tall", tall, has_face=False, has_text=True)
    loaded = read_protected_image("folder", "tall")
    assert loaded is not None
    bgr, faces, texts = loaded
    assert bgr.shape[1] < bgr.shape[0]
    assert bgr.shape[0] <= 1080
    assert abs((bgr.shape[0] / bgr.shape[1]) - 4.0) < 0.05
    assert faces is False
    assert texts is True
    assert read_protected_image("folder", "missing") is None
