from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps
from PIL.ExifTags import GPSTAGS, TAGS

from stream_media_viewer.config import SUPPORTED_IMAGE_SUFFIXES, SUPPORTED_VIDEO_SUFFIXES
from stream_media_viewer.library.item import MediaItem

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


def _exif_datetime_and_gps(path: Path) -> tuple[datetime | None, bool]:
    if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES | {".heic", ".heif"}:
        return None, False
    try:
        with Image.open(path) as img:
            raw = img.getexif()
    except OSError:
        return None, False
    if not raw:
        return None, False
    captured: datetime | None = None
    has_gps = False
    named = {TAGS.get(k, k): v for k, v in raw.items()}
    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
        value = named.get(key)
        if isinstance(value, str):
            try:
                captured = datetime.strptime(value.strip().split(".")[0], "%Y:%m:%d %H:%M:%S")
                break
            except ValueError:
                continue
    gps_ifd = raw.get_ifd(0x8825) if hasattr(raw, "get_ifd") else None
    if gps_ifd:
        labels = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
        has_gps = bool(labels.get("GPSLatitude") and labels.get("GPSLongitude"))
    return captured, has_gps


def scan_folder(folder: Path) -> list[MediaItem]:
    if not folder.is_dir():
        return []
    items: list[MediaItem] = []
    suffixes = SUPPORTED_IMAGE_SUFFIXES | SUPPORTED_VIDEO_SUFFIXES
    for path in folder.iterdir():
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in suffixes:
            continue
        kind = "video" if suffix in SUPPORTED_VIDEO_SUFFIXES else "image"
        captured, has_gps = _exif_datetime_and_gps(path)
        items.append(
            MediaItem(path=path, kind=kind, captured_at=captured, has_gps=has_gps, readable=True)
        )
    items.sort(
        key=lambda it: (
            it.captured_at is None,
            it.captured_at or datetime.min,
            it.path.name.lower(),
        )
    )
    return items


def load_rgb_image(path: Path) -> Image.Image | None:
    try:
        image = Image.open(path)
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")
    except OSError:
        return None
