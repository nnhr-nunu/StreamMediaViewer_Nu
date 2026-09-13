"""アプリ定数。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "StreamMediaViewer_Nu"
SETTINGS_FILENAME = "settings.json"

DEFAULT_KEYMAP = {
    "preview_next": "D",
    "preview_prev": "A",
    "send_to_output": "Return",
    "send_to_output_alt": "Ctrl+Return",
    "panic": "0",
    "panic_alt": "Esc",
    "play_pause": "Space",
    "play_pause_numpad": "5",
    "toggle_favorite": "F",
    "undo_manual_blur": "Ctrl+Z",
}

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif"}
SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def user_config_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_DIR_NAME
    return Path.home() / ".local" / "share" / APP_DIR_NAME
