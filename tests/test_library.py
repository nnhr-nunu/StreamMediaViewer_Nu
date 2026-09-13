from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer.library.item import FileNote
from stream_media_viewer.library.scan import load_rgb_image, scan_folder
from stream_media_viewer.render.canvas import OUTPUT_HEIGHT, OUTPUT_WIDTH, fit_letterbox


def test_scan_sorts_by_name_when_no_exif(tmp_path: Path) -> None:
    for name in ("b.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / name)
    (tmp_path / "skip.txt").write_text("x")
    items = scan_folder(tmp_path)
    assert [it.path.name for it in items] == ["a.jpg", "b.jpg"]
    assert all(it.kind == "image" for it in items)


def test_scan_reports_progress(tmp_path: Path) -> None:
    for name in ("b.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / name)
    seen: list[tuple[int, int]] = []
    items = scan_folder(tmp_path, progress=lambda done, total: seen.append((done, total)))
    assert len(items) == 2
    assert seen[0] == (0, 2)
    assert seen[-1] == (2, 2)


def test_scan_reads_nested_folders_when_recursive(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "root.jpg")
    nested = tmp_path / "day1"
    nested.mkdir()
    Image.new("RGB", (8, 8), (40, 50, 60)).save(nested / "inner.jpg")
    with_nested = scan_folder(tmp_path, recursive=True)
    names = {it.path.name: it.relative_folder for it in with_nested}
    assert names["root.jpg"] == ""
    assert names["inner.jpg"] == "day1"
    top_only = scan_folder(tmp_path, recursive=False)
    assert [it.path.name for it in top_only] == ["root.jpg"]


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


def test_scan_reads_mp4_creation_time(tmp_path: Path) -> None:
    from datetime import datetime

    created = datetime(2024, 4, 1, 12, 0, 0)
    epoch = datetime(1904, 1, 1)
    seconds = int((created - epoch).total_seconds())
    mvhd = (8 + 24).to_bytes(4, "big") + b"mvhd" + b"\x00\x00\x00\x00" + seconds.to_bytes(
        4, "big"
    ) + b"\x00" * 16
    moov = (8 + len(mvhd)).to_bytes(4, "big") + b"moov" + mvhd
    ftyp = (8 + 12).to_bytes(4, "big") + b"ftyp" + b"isom" + b"\x00" * 8
    (tmp_path / "clip.mp4").write_bytes(ftyp + moov)
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "z.jpg")
    items = scan_folder(tmp_path)
    names = [it.path.name for it in items]
    assert names[0] == "clip.mp4"
    assert items[0].captured_at is not None
    assert items[0].captured_at.year == 2024


def test_load_rgb_image_caps_long_edge(tmp_path: Path) -> None:
    Image.new("RGB", (4000, 2000), (10, 20, 30)).save(tmp_path / "big.jpg")
    image = load_rgb_image(tmp_path / "big.jpg")
    assert image is not None
    assert max(image.size) <= 1920


def test_letterbox_is_1920x1080() -> None:
    src = np.zeros((100, 400, 3), dtype=np.uint8)
    src[:] = (0, 255, 0)
    out = fit_letterbox(src)
    assert out.shape == (OUTPUT_HEIGHT, OUTPUT_WIDTH, 3)
    assert out[0, 0].tolist() == [0, 0, 0]
    assert int(out[OUTPUT_HEIGHT // 2, OUTPUT_WIDTH // 2, 1]) > 0
