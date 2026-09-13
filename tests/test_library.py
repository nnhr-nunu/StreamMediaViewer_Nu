from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer.library.item import FileNote
from stream_media_viewer.library.scan import scan_folder
from stream_media_viewer.render.canvas import OUTPUT_HEIGHT, OUTPUT_WIDTH, fit_letterbox


def test_scan_sorts_by_name_when_no_exif(tmp_path: Path) -> None:
    for name in ("b.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / name)
    (tmp_path / "skip.txt").write_text("x")
    items = scan_folder(tmp_path)
    assert [it.path.name for it in items] == ["a.jpg", "b.jpg"]
    assert all(it.kind == "image" for it in items)


def test_file_note_keeps_detection_flags() -> None:
    note = FileNote(has_face=True, has_text_region=True)
    restored = FileNote.from_dict(note.to_dict())
    assert restored.has_face is True
    assert restored.has_text_region is True


def test_scan_skips_empty_and_corrupt_images(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    (tmp_path / "empty.jpg").write_bytes(b"")
    (tmp_path / "bad.jpg").write_bytes(b"not-an-image")
    items = scan_folder(tmp_path)
    assert [it.path.name for it in items] == ["good.jpg"]


def test_letterbox_is_1920x1080() -> None:
    src = np.zeros((100, 400, 3), dtype=np.uint8)
    src[:] = (0, 255, 0)
    out = fit_letterbox(src)
    assert out.shape == (OUTPUT_HEIGHT, OUTPUT_WIDTH, 3)
    assert out[0, 0].tolist() == [0, 0, 0]
    assert int(out[OUTPUT_HEIGHT // 2, OUTPUT_WIDTH // 2, 1]) > 0
