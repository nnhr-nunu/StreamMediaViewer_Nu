from pathlib import Path

from PIL import Image

from stream_media_viewer.library.protect_cache import ProtectFrameCache
from stream_media_viewer.library.thumbs import ensure_thumb
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
