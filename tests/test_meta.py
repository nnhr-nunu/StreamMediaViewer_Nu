from datetime import datetime, timedelta
from pathlib import Path

from stream_media_viewer.library.geo import gps_to_decimal, place_from_gps
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
    assert format_place_name("伏見", "京都", "日本") == "伏見 京都 日本"


def test_gps_becomes_nearby_city_name_not_coordinates() -> None:
    lat = gps_to_decimal(((35, 1), (0, 1), (41.8, 1)), "N")
    lon = gps_to_decimal(((135, 1), (46, 1), (5.0, 1)), "E")
    assert lat is not None
    assert lon is not None
    name = place_from_gps(lat, lon)
    assert name == "京都"
    assert "135" not in name
    assert "35" not in name


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
