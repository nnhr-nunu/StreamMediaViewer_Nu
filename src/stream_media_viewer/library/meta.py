"""写真・動画から日時と場所名を取る。座標の数字は返さない。"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, IptcImagePlugin
from PIL.ExifTags import GPSTAGS, TAGS

from stream_media_viewer.config import SUPPORTED_IMAGE_SUFFIXES, SUPPORTED_VIDEO_SUFFIXES

_MAC_EPOCH = datetime(1904, 1, 1)
_MIN_YEAR = 1990
_MAX_YEAR = 2100


def format_place_name(city: str, country: str) -> str:
    parts = [part.strip() for part in (city, country) if part and part.strip()]
    return " ".join(parts)


def _decode_iptc(value: object) -> str:
    if isinstance(value, bytes):
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                return value.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return ""
    if isinstance(value, str):
        return value.strip()
    return ""


def place_name_from_iptc(info: dict | None) -> str:
    if not info:
        return ""
    city = _decode_iptc(info.get((2, 90)))
    country = _decode_iptc(info.get((2, 101)))
    return format_place_name(city, country)


def _parse_exif_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip().split(".")[0], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def image_capture_meta(path: Path) -> tuple[datetime | None, bool, str]:
    if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES | {".heic", ".heif"}:
        return None, False, ""
    try:
        with Image.open(path) as img:
            raw = img.getexif()
            try:
                iptc = IptcImagePlugin.getiptcinfo(img)
            except Exception:
                iptc = None
    except OSError:
        return None, False, ""
    captured: datetime | None = None
    has_gps = False
    if raw:
        named = {TAGS.get(k, k): v for k, v in raw.items()}
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            captured = _parse_exif_datetime(named.get(key))
            if captured:
                break
        gps_ifd = raw.get_ifd(0x8825) if hasattr(raw, "get_ifd") else None
        if gps_ifd:
            labels = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            has_gps = bool(labels.get("GPSLatitude") and labels.get("GPSLongitude"))
    return captured, has_gps, place_name_from_iptc(iptc)


def _read_box_header(handle, file_end: int) -> tuple[bytes, int, int] | None:
    start = handle.tell()
    header = handle.read(8)
    if len(header) < 8:
        return None
    size = int.from_bytes(header[:4], "big")
    kind = header[4:8]
    header_len = 8
    if size == 1:
        large = handle.read(8)
        if len(large) < 8:
            return None
        size = int.from_bytes(large, "big")
        header_len = 16
    elif size == 0:
        size = file_end - start
    if size < header_len or start + size > file_end:
        return None
    return kind, start + header_len, start + size


def _sane(dt: datetime) -> datetime | None:
    if dt.year < _MIN_YEAR or dt.year > _MAX_YEAR:
        return None
    return dt


def _mvhd_time(payload: bytes) -> datetime | None:
    if len(payload) < 8:
        return None
    version = payload[0]
    if version == 1:
        if len(payload) < 20:
            return None
        seconds = int.from_bytes(payload[4:12], "big")
    else:
        seconds = int.from_bytes(payload[4:8], "big")
    if seconds <= 0:
        return None
    try:
        return _sane(_MAC_EPOCH + timedelta(seconds=seconds))
    except OverflowError:
        return None


def mp4_creation_datetime(path: Path) -> datetime | None:
    try:
        file_end = path.stat().st_size
        with path.open("rb") as handle:
            return _scan_moov(handle, 0, file_end, file_end)
    except OSError:
        return None


def _scan_moov(handle, start: int, end: int, file_end: int, *, depth: int = 0) -> datetime | None:
    if depth > 6:
        return None
    handle.seek(start)
    while handle.tell() + 8 <= end:
        header = _read_box_header(handle, file_end)
        if header is None:
            return None
        kind, payload_start, payload_end = header
        if kind in {b"moov", b"trak", b"mdia"}:
            found = _scan_moov(handle, payload_start, payload_end, file_end, depth=depth + 1)
            if found:
                return found
        elif kind == b"mvhd":
            handle.seek(payload_start)
            payload = handle.read(min(32, payload_end - payload_start))
            found = _mvhd_time(payload)
            if found:
                return found
        handle.seek(payload_end)
    return None


def video_captured_at(path: Path) -> datetime | None:
    if path.suffix.lower() not in SUPPORTED_VIDEO_SUFFIXES:
        return None
    if path.suffix.lower() in {".mp4", ".mov", ".m4v"}:
        found = mp4_creation_datetime(path)
        if found:
            return found
    return None
