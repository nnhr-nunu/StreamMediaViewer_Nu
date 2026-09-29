from pathlib import Path

import numpy as np

from stream_media_viewer.render.image_io import read_bgr, write_jpeg


def test_jpeg_roundtrip_under_japanese_folder(tmp_path: Path) -> None:
    folder = tmp_path / "ユーザー名" / "下準備"
    folder.mkdir(parents=True)
    path = folder / "000000.jpg"
    bgr = np.full((24, 32, 3), 128, dtype=np.uint8)
    assert write_jpeg(path, bgr, 90) is True
    loaded = read_bgr(path)
    assert loaded is not None
    assert loaded.shape == bgr.shape


def test_read_missing_or_empty_file_returns_none(tmp_path: Path) -> None:
    assert read_bgr(tmp_path / "none.jpg") is None
    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    assert read_bgr(empty) is None
