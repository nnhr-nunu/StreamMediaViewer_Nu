from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from stream_media_viewer.config import SUPPORTED_IMAGE_SUFFIXES, SUPPORTED_VIDEO_SUFFIXES
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.meta import image_capture_meta, video_captured_at

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


def _file_has_bytes(path: Path) -> bool:
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def _image_readable(path: Path) -> bool:
    if not _file_has_bytes(path):
        return False
    try:
        with Image.open(path) as img:
            img.verify()
    except (OSError, ValueError, SyntaxError):
        return False
    return True


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
        if kind == "image" and not _image_readable(path):
            continue
        if kind == "video" and not _file_has_bytes(path):
            continue
        if kind == "image":
            captured, has_gps, place_name = image_capture_meta(path)
        else:
            captured = video_captured_at(path)
            has_gps = False
            place_name = ""
        items.append(
            MediaItem(
                path=path,
                kind=kind,
                captured_at=captured,
                has_gps=has_gps,
                readable=True,
                place_name=place_name,
            )
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
