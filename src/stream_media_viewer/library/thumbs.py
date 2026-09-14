"""操作画面の一覧用縮小画。配信用の窓には出さない。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from stream_media_viewer.config import SUPPORTED_VIDEO_SUFFIXES, user_config_dir
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.scan import load_rgb_image, video_header_ok

THUMB_SIZE = 480


def thumb_paths_for(
    items: list[MediaItem],
    *,
    photos: bool,
    videos: bool,
) -> list[Path]:
    paths: list[Path] = []
    for item in items:
        if item.kind == "image" and photos:
            paths.append(item.path)
        elif item.kind == "video" and videos:
            paths.append(item.path)
    return paths


def thumbs_root() -> Path:
    root = user_config_dir() / "thumbs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def thumb_cache_path(src: Path) -> Path:
    try:
        stat = src.stat()
        stamp = f"{src.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{THUMB_SIZE}"
    except OSError:
        stamp = str(src)
    digest = hashlib.sha1(stamp.encode("utf-8")).hexdigest()
    return thumbs_root() / f"{digest}.jpg"


def _first_video_frame(src: Path) -> Image.Image | None:
    import cv2

    if not video_header_ok(src):
        return None
    cap = cv2.VideoCapture(str(src))
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    image.thumbnail((THUMB_SIZE * 2, THUMB_SIZE * 2), Image.Resampling.BILINEAR)
    return image


def ensure_thumb(src: Path) -> Path | None:
    dest = thumb_cache_path(src)
    if dest.is_file():
        return dest
    if src.suffix.lower() in SUPPORTED_VIDEO_SUFFIXES:
        image = _first_video_frame(src)
    else:
        image = load_rgb_image(src, max_side=THUMB_SIZE * 2)
    if image is None:
        return None
    image.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.BILINEAR)
    try:
        image.save(dest, "JPEG", quality=72)
    except OSError:
        return None
    return dest
