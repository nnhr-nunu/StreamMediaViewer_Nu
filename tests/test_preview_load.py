from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer.library.preview_load import ImageLoadWorker


def test_image_load_worker_emits_bgr(qtbot, tmp_path: Path) -> None:
    src = tmp_path / "a.jpg"
    Image.new("RGB", (12, 8), (10, 20, 30)).save(src)
    got: list[tuple[tuple[int, ...], int]] = []
    worker = ImageLoadWorker(src, 4)
    worker.loaded.connect(lambda bgr, seq: got.append((tuple(bgr.shape), int(seq))))
    worker.start()
    qtbot.waitUntil(lambda: bool(got), timeout=5000)
    assert got[0][1] == 4
    assert got[0][0][2] == 3
    assert got[0][0][0] == 8
    assert got[0][0][1] == 12
