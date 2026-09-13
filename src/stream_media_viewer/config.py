"""アプリ定数。仕様が固まるまでの初期値。"""

from pathlib import Path

APP_DIR_NAME = "StreamMediaViewer_Nu"
SETTINGS_FILENAME = "settings.json"

DEFAULT_KEYMAP = {
    "preview_next": "D",
    "preview_prev": "A",
    "send_to_output": "Return",
    "send_to_output_alt": "Ctrl+Return",
    "panic": "Space",
    "panic_alt": "Esc",
    "toggle_favorite": "F",
    "undo_manual_blur": "Ctrl+Z",
}

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def user_config_dir() -> Path:
    return Path.home() / "AppData" / "Local" / APP_DIR_NAME
