from pathlib import Path

from PIL import Image

from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.protect_cache import ProtectFrameCache
from stream_media_viewer.library.thumbs import ensure_thumb, thumb_paths_for
import numpy as np


def test_ensure_thumb_writes_jpeg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "stream_media_viewer.library.thumbs.user_config_dir", lambda: tmp_path
    )
    src = tmp_path / "shot.jpg"
    Image.new("RGB", (400, 300), (10, 20, 30)).save(src)
    dest = ensure_thumb(src)
    assert dest is not None
    assert dest.is_file()
    again = ensure_thumb(src)
    assert again == dest


def test_thumb_paths_for_skips_videos_until_asked(tmp_path: Path) -> None:
    photo = MediaItem(path=tmp_path / "a.jpg", kind="image", captured_at=None, has_gps=False)
    video = MediaItem(path=tmp_path / "clip.mp4", kind="video", captured_at=None, has_gps=False)
    only_photos = thumb_paths_for([photo, video], photos=True, videos=False)
    assert only_photos == [photo.path]
    both = thumb_paths_for([photo, video], photos=True, videos=True)
    assert both == [photo.path, video.path]


def test_protect_frame_cache_evicts_oldest() -> None:
    cache = ProtectFrameCache(limit=2)
    a = np.zeros((2, 2, 3), dtype=np.uint8)
    b = np.ones((2, 2, 3), dtype=np.uint8)
    c = np.full((2, 2, 3), 3, dtype=np.uint8)
    cache.put("a", a, False, False)
    cache.put("b", b, True, False)
    cache.put("c", c, False, True)
    assert cache.get("a") is None
    hit = cache.get("b")
    assert hit is not None
    assert hit[1] is True


def test_protect_frame_cache_reports_room() -> None:
    cache = ProtectFrameCache(limit=3)
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    assert cache.room() == 3
    cache.put("a", frame, False, False)
    assert cache.has("a") is True
    assert cache.has("b") is False
    assert cache.room() == 2
    cache.put("b", frame, False, False)
    cache.put("c", frame, False, False)
    assert cache.room() == 0
    assert len(cache) == 3


def test_protect_frame_cache_default_holds_sixteen() -> None:
    cache = ProtectFrameCache()
    assert cache.room() == 16
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    for index in range(16):
        cache.put(str(index), frame, False, False)
    assert cache.room() == 0
    assert len(cache) == 16
