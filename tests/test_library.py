from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer.library.item import FileNote, MediaItem
from stream_media_viewer.library.scan import load_rgb_image, merge_media_items, scan_folder
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
    assert seen[-1] == (2, 2)
    assert any(total == 2 for _done, total in seen)


def test_scan_reports_found_before_reading_exif(tmp_path: Path, monkeypatch) -> None:
    for name in ("b.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / name)
    order: list[str] = []

    def on_found(items: list) -> None:
        order.append("found")
        assert len(items) == 2

    def slow_meta(path: Path):
        order.append("meta")
        return None, False, ""

    monkeypatch.setattr("stream_media_viewer.library.scan.image_capture_meta", slow_meta)
    items = scan_folder(tmp_path, kinds={"image"}, on_found=on_found)
    assert order[0] == "found"
    assert order.count("meta") == 2
    assert [it.path.name for it in items] == ["a.jpg", "b.jpg"]


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


def test_file_note_keeps_hidden() -> None:
    note = FileNote(hidden=True)
    restored = FileNote.from_dict(note.to_dict())
    assert restored.hidden is True
    assert FileNote.from_dict({}).hidden is False


def test_file_note_keeps_rotation() -> None:
    note = FileNote(rotation=270)
    restored = FileNote.from_dict(note.to_dict())
    assert restored.rotation == 270
    assert FileNote.from_dict({"rotation": 45}).rotation == 0


def test_file_note_bad_timings_fall_back() -> None:
    note = FileNote.from_dict({"in_ms": "nope", "out_ms": "x", "rotation": "turn"})
    assert note.in_ms == 0
    assert note.out_ms is None
    assert note.rotation == 0


def test_scan_skips_empty_and_corrupt_images(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    (tmp_path / "empty.jpg").write_bytes(b"")
    (tmp_path / "bad.jpg").write_bytes(b"not-an-image")
    items = scan_folder(tmp_path)
    assert [it.path.name for it in items] == ["good.jpg"]


def test_scan_skips_corrupt_videos(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "good.jpg")
    (tmp_path / "broken.mp4").write_bytes(b"not-a-video")
    items = scan_folder(tmp_path)
    assert [it.path.name for it in items] == ["good.jpg"]


def _tiny_mp4(path: Path) -> None:
    from datetime import datetime

    created = datetime(2024, 4, 1, 12, 0, 0)
    epoch = datetime(1904, 1, 1)
    seconds = int((created - epoch).total_seconds())
    mvhd = (8 + 24).to_bytes(4, "big") + b"mvhd" + b"\x00\x00\x00\x00" + seconds.to_bytes(
        4, "big"
    ) + b"\x00" * 16
    moov = (8 + len(mvhd)).to_bytes(4, "big") + b"moov" + mvhd
    ftyp = (8 + 12).to_bytes(4, "big") + b"ftyp" + b"isom" + b"\x00" * 8
    path.write_bytes(ftyp + moov)


def test_scan_reads_mp4_creation_time(tmp_path: Path) -> None:
    _tiny_mp4(tmp_path / "clip.mp4")
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "z.jpg")
    items = scan_folder(tmp_path)
    names = [it.path.name for it in items]
    assert names[0] == "clip.mp4"
    assert items[0].captured_at is not None
    assert items[0].captured_at.year == 2024


def test_scan_folder_can_skip_videos(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(tmp_path / "a.jpg")
    _tiny_mp4(tmp_path / "clip.mp4")
    photos = scan_folder(tmp_path, kinds={"image"})
    assert [it.path.name for it in photos] == ["a.jpg"]
    videos = scan_folder(tmp_path, kinds={"video"})
    assert [it.path.name for it in videos] == ["clip.mp4"]


def test_merge_media_items_appends_without_duplicates(tmp_path: Path) -> None:
    photo = MediaItem(
        path=tmp_path / "a.jpg",
        kind="image",
        captured_at=None,
        has_gps=False,
    )
    video = MediaItem(
        path=tmp_path / "clip.mp4",
        kind="video",
        captured_at=None,
        has_gps=False,
    )
    again = MediaItem(
        path=tmp_path / "a.jpg",
        kind="image",
        captured_at=None,
        has_gps=True,
    )
    merged = merge_media_items([photo], [video, again])
    names = [it.path.name for it in merged]
    assert names.count("a.jpg") == 1
    assert "clip.mp4" in names
    assert next(it.has_gps for it in merged if it.path.name == "a.jpg") is True


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
