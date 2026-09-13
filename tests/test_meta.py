from datetime import datetime, timedelta
from pathlib import Path

from stream_media_viewer.library.meta import (
    format_place_name,
    mp4_creation_datetime,
)


def _box(kind: bytes, payload: bytes) -> bytes:
    return (8 + len(payload)).to_bytes(4, "big") + kind + payload


def test_format_place_name_joins_city_and_country() -> None:
    assert format_place_name("京都", "日本") == "京都 日本"
    assert format_place_name("京都", "") == "京都"
    assert format_place_name("", "") == ""


def test_mp4_creation_datetime_reads_mvhd(tmp_path: Path) -> None:
    created = datetime(2024, 4, 1, 12, 0, 0)
    epoch = datetime(1904, 1, 1)
    seconds = int((created - epoch).total_seconds())
    mvhd = _box(
        b"mvhd",
        b"\x00\x00\x00\x00" + seconds.to_bytes(4, "big") + b"\x00" * 20,
    )
    moov = _box(b"moov", mvhd)
    ftyp = _box(b"ftyp", b"isom" + b"\x00" * 8)
    path = tmp_path / "clip.mp4"
    path.write_bytes(ftyp + moov)
    got = mp4_creation_datetime(path)
    assert got is not None
    assert abs((got - created) - timedelta(0)) < timedelta(seconds=2)
