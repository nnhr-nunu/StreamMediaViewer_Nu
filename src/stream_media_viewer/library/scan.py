from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def video_header_ok(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return False
    if len(head) < 8:
        return False
    suffix = path.suffix.lower()
    if suffix in {".mp4", ".mov", ".m4v"}:
        return head[4:8] == b"ftyp"
    if suffix in {".webm", ".mkv"}:
        return head.startswith(b"\x1a\x45\xdf\xa3")
    if suffix == ".avi":
        return head.startswith(b"RIFF") and b"AVI" in head
    return False


def _iter_files(folder: Path, *, recursive: bool):
    if recursive:
        yield from folder.rglob("*")
        return
    yield from folder.iterdir()


def merge_media_items(existing: list[MediaItem], incoming: list[MediaItem]) -> list[MediaItem]:
    by_key: dict[str, MediaItem] = {}
    for item in existing:
        by_key[str(item.path)] = item
    for item in incoming:
        by_key[str(item.path)] = item
    return list(by_key.values())


def sort_media_items(items: list[MediaItem]) -> None:
    items.sort(
        key=lambda it: (
            it.captured_at is None,
            it.captured_at or datetime.min,
            it.relative_folder.lower(),
            it.path.name.lower(),
        )
    )


def _fill_capture_meta(item: MediaItem) -> None:
    if item.kind == "image":
        captured, has_gps, place_name = image_capture_meta(item.path)
    else:
        captured = video_captured_at(item.path)
        has_gps = False
        place_name = ""
    item.captured_at = captured
    item.has_gps = has_gps
    item.place_name = place_name


def scan_folder(
    folder: Path,
    *,
    recursive: bool = True,
    progress: Callable[[int, int], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    kinds: Iterable[str] | None = None,
    on_found: Callable[[list[MediaItem]], None] | None = None,
) -> list[MediaItem]:
    if not folder.is_dir():
        return []
    wanted = frozenset(kinds) if kinds is not None else frozenset({"image", "video"})
    suffixes = SUPPORTED_IMAGE_SUFFIXES | SUPPORTED_VIDEO_SUFFIXES
    paths: list[Path] = []
    found = 0
    for path in _iter_files(folder, recursive=recursive):
        if should_stop and should_stop():
            return []
        if not path.is_file() or _hidden_part(path, folder):
            continue
        suffix = path.suffix.lower()
        if suffix not in suffixes:
            continue
        if not _file_has_bytes(path):
            continue
        kind = "video" if suffix in SUPPORTED_VIDEO_SUFFIXES else "image"
        if kind not in wanted:
            continue
        if kind == "image" and not _image_header_ok(path):
            continue
        if kind == "video" and not video_header_ok(path):
            continue
        paths.append(path)
        found += 1
        if progress and found % 8 == 0:
            progress(found, 0)
    items: list[MediaItem] = []
    for path in paths:
        suffix = path.suffix.lower()
        kind = "video" if suffix in SUPPORTED_VIDEO_SUFFIXES else "image"
        items.append(
            MediaItem(
                path=path,
                kind=kind,
                captured_at=None,
                has_gps=False,
                readable=True,
                relative_folder=relative_folder(folder, path),
            )
        )
    sort_media_items(items)
    if on_found:
        on_found(items)
    total = len(items)
    if progress:
        progress(0, total)
    if total:
        workers = min(8, total)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fill_capture_meta, item) for item in items]
            done_n = 0
            for fut in as_completed(futures):
                if should_stop and should_stop():
                    return []
                fut.result()
                done_n += 1
                if progress:
                    progress(done_n, total)
    sort_media_items(items)
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
