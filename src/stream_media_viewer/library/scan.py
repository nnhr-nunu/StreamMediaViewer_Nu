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

PREVIEW_MAX_SIDE = 1920


def _file_has_bytes(path: Path) -> bool:
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def _hidden_part(path: Path, root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return any(part.startswith(".") for part in rel.parts)


def relative_folder(root: Path, path: Path) -> str:
    try:
        parent = path.parent.resolve().relative_to(root.resolve())
    except ValueError:
        return ""
    text = parent.as_posix()
    return "" if text in {".", ""} else text


def _image_header_ok(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return False
    if len(head) < 4:
        return False
    if head.startswith(b"\xff\xd8") or head.startswith(b"\x89PNG") or head.startswith(b"BM"):
        return True
    if head[:4] == b"RIFF" and b"WEBP" in head:
        return True
    return head[4:8] == b"ftyp"


def _iter_files(folder: Path, *, recursive: bool):
    if recursive:
        yield from folder.rglob("*")
        return
    yield from folder.iterdir()


def scan_folder(folder: Path, *, recursive: bool = True) -> list[MediaItem]:
    if not folder.is_dir():
        return []
    items: list[MediaItem] = []
    suffixes = SUPPORTED_IMAGE_SUFFIXES | SUPPORTED_VIDEO_SUFFIXES
    for path in _iter_files(folder, recursive=recursive):
        if not path.is_file() or _hidden_part(path, folder):
            continue
        suffix = path.suffix.lower()
        if suffix not in suffixes:
            continue
        kind = "video" if suffix in SUPPORTED_VIDEO_SUFFIXES else "image"
        if not _file_has_bytes(path):
            continue
        if kind == "image" and not _image_header_ok(path):
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
                relative_folder=relative_folder(folder, path),
            )
        )
    items.sort(
        key=lambda it: (
            it.captured_at is None,
            it.captured_at or datetime.min,
            it.relative_folder.lower(),
            it.path.name.lower(),
        )
    )
    return items


def load_rgb_image(path: Path, *, max_side: int = PREVIEW_MAX_SIDE) -> Image.Image | None:
    try:
        image = Image.open(path)
        if hasattr(image, "draft"):
            image.draft("RGB", (max_side, max_side))
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
        return image.convert("RGB")
    except OSError:
        return None
