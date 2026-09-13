"""写真・動画から日時と場所名を取る。座標の数字は返さない。"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, IptcImagePlugin
from PIL.ExifTags import GPSTAGS, TAGS

from stream_media_viewer.config import SUPPORTED_IMAGE_SUFFIXES, SUPPORTED_VIDEO_SUFFIXES
from stream_media_viewer.library.geo import gps_to_decimal, place_from_gps

_MAC_EPOCH = datetime(1904, 1, 1)
_MIN_YEAR = 1990
_MAX_YEAR = 2100


def format_place_name(*parts: str) -> str:
    seen: list[str] = []
    for part in parts:
        text = part.strip()
        if text and text not in seen:
            seen.append(text)
    return " ".join(seen)


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
    sub = _decode_iptc(info.get((2, 92)))
    city = _decode_iptc(info.get((2, 90)))
    province = _decode_iptc(info.get((2, 95)))
    country = _decode_iptc(info.get((2, 101)))
    return format_place_name(sub, city, province, country)


def _xmp_texts(node: object, found: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_l = str(key).lower()
            if "gps" in key_l or "lat" in key_l or "lon" in key_l or "coord" in key_l:
                _xmp_texts(value, found)
                continue
            if any(
                token in key_l for token in ("city", "country", "location", "state", "province")
            ):
                if isinstance(value, str) and value.strip():
                    found.append(value.strip())
            _xmp_texts(value, found)
    elif isinstance(node, list):
        for item in node:
            _xmp_texts(item, found)


def place_name_from_xmp(xmp: dict | None) -> str:
    if not xmp:
        return ""
    found: list[str] = []
    _xmp_texts(xmp, found)
    return format_place_name(*found[:4])


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
            xmp = None
            if hasattr(img, "getxmp") and importlib.util.find_spec("defusedxml"):
                try:
                    xmp = img.getxmp()
                except Exception:
                    xmp = None
    except OSError:
        return None, False, ""
    captured: datetime | None = None
    has_gps = False
    gps_place = ""
    if raw:
        named = {TAGS.get(k, k): v for k, v in raw.items()}
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            captured = _parse_exif_datetime(named.get(key))
            if captured:
                break
        gps_ifd = raw.get_ifd(0x8825) if hasattr(raw, "get_ifd") else None
        if gps_ifd:
            labels = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            lat = gps_to_decimal(
                labels.get("GPSLatitude"), str(labels.get("GPSLatitudeRef") or "N")
            )
            lon = gps_to_decimal(
                labels.get("GPSLongitude"), str(labels.get("GPSLongitudeRef") or "E")
            )
            has_gps = lat is not None and lon is not None
            area = labels.get("GPSAreaInformation")
            if isinstance(area, bytes):
                gps_place = area.decode("utf-8", "ignore").strip("\x00 ").strip()
            elif isinstance(area, str):
                gps_place = area.strip()
            if has_gps and lat is not None and lon is not None and not gps_place:
                gps_place = place_from_gps(lat, lon)
    place = (
        place_name_from_iptc(iptc)
        or place_name_from_xmp(xmp if isinstance(xmp, dict) else None)
        or gps_place
    )
    return captured, has_gps, place


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
