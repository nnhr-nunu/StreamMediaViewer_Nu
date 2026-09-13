"""設定の読み書き。配信出力にはメタデータを載せない。"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from stream_media_viewer.config import (
    DEFAULT_KEYMAP,
    SETTINGS_FILENAME,
    user_config_dir,
)


@dataclass
class AppSettings:
    last_folder: str = ""
    blur_strength: int = 25
    keymap: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KEYMAP))
    favorites: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        keymap = dict(DEFAULT_KEYMAP)
        raw_map = data.get("keymap") or {}
        if isinstance(raw_map, dict):
            keymap.update({str(k): str(v) for k, v in raw_map.items()})
        favorites = data.get("favorites") or []
        if not isinstance(favorites, list):
            favorites = []
        return cls(
            last_folder=str(data.get("last_folder") or ""),
            blur_strength=int(data.get("blur_strength") or 25),
            keymap=keymap,
            favorites=[str(x) for x in favorites],
        )


def settings_path() -> Path:
    """ポータブル exe は実行ファイル隣、開発時はユーザー設定フォルダ。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / SETTINGS_FILENAME
    directory = user_config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / SETTINGS_FILENAME


def load_settings(path: Path | None = None) -> AppSettings:
    target = path or settings_path()
    if not target.is_file():
        return AppSettings()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()
    if not isinstance(raw, dict):
        return AppSettings()
    return AppSettings.from_dict(raw)


def save_settings(settings: AppSettings, path: Path | None = None) -> Path:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target
