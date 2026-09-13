"""設定の読み書き。配信出力にはメタデータを載せない。"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stream_media_viewer.config import SETTINGS_FILENAME, user_config_dir
from stream_media_viewer.detect.blur import (
    DEFAULT_BLUR_STRENGTH,
    DEFAULT_BRUSH_WIDTH,
    MAX_BLUR_STRENGTH,
    MAX_BRUSH_WIDTH,
    MIN_BLUR_STRENGTH,
    MIN_BRUSH_WIDTH,
)
from stream_media_viewer.library.item import FileNote
from stream_media_viewer.library.sort import parse_list_sort
from stream_media_viewer.render.enhance import parse_enhance_level

RECENT_FOLDER_LIMIT = 8


def clamp_blur_strength(raw: Any) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_BLUR_STRENGTH
    value = max(MIN_BLUR_STRENGTH, min(MAX_BLUR_STRENGTH, value))
    return value


def clamp_brush_width(raw: Any) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_BRUSH_WIDTH
    return max(MIN_BRUSH_WIDTH, min(MAX_BRUSH_WIDTH, value))


def remember_folder(recent: list[str], path: str, *, limit: int = RECENT_FOLDER_LIMIT) -> list[str]:
    incoming = str(path).strip()
    if not incoming:
        return list(recent)[:limit]
    incoming_key = incoming.replace("\\", "/").rstrip("/").casefold()
    ordered = [incoming]
    for item in recent:
        key = str(item).replace("\\", "/").rstrip("/").casefold()
        if key != incoming_key:
            ordered.append(item)
    return ordered[:limit]


@dataclass
class AppSettings:
    last_folder: str = ""
    blur_strength: int = DEFAULT_BLUR_STRENGTH
    language: str = "ja"
    face_blur: bool = True
    text_blur: bool = False
    video_audio: bool = False
    enhance_level: str = "weak"
    standby_path: str = ""
    use_standby: bool = False
    operator_geometry: str = ""
    output_pos: str = ""
    date_from: str = ""
    date_to: str = ""
    notes: dict[str, FileNote] = field(default_factory=dict)
    blur_off_confirmed: bool = False
    recent_folders: list[str] = field(default_factory=list)
    include_subfolders: bool = True
    brush_width: int = DEFAULT_BRUSH_WIDTH
    list_sort: str = "date_asc"
    false_face_hashes: list[str] = field(default_factory=list)

    def note_for(self, path: str) -> FileNote:
        note = self.notes.get(path)
        if note is None:
            note = FileNote()
            self.notes[path] = note
        return note

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_folder": self.last_folder,
            "blur_strength": self.blur_strength,
            "language": self.language,
            "face_blur": self.face_blur,
            "text_blur": self.text_blur,
            "video_audio": self.video_audio,
            "enhance_level": self.enhance_level,
            "standby_path": self.standby_path,
            "use_standby": self.use_standby,
            "operator_geometry": self.operator_geometry,
            "output_pos": self.output_pos,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "blur_off_confirmed": self.blur_off_confirmed,
            "recent_folders": list(self.recent_folders),
            "include_subfolders": self.include_subfolders,
            "brush_width": self.brush_width,
            "list_sort": self.list_sort,
            "false_face_hashes": list(self.false_face_hashes),
            "notes": {key: note.to_dict() for key, note in self.notes.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        raw_notes = data.get("notes") or {}
        notes: dict[str, FileNote] = {}
        if isinstance(raw_notes, dict):
            for key, value in raw_notes.items():
                if isinstance(value, dict):
                    notes[str(key)] = FileNote.from_dict(value)
        raw_recent = data.get("recent_folders") or []
        recent_folders: list[str] = []
        if isinstance(raw_recent, list):
            recent_folders = [str(item) for item in raw_recent if str(item).strip()]
        last_folder = str(data.get("last_folder") or "")
        if last_folder:
            recent_folders = remember_folder(recent_folders, last_folder)
        raw_hashes = data.get("false_face_hashes") or []
        false_face_hashes: list[str] = []
        if isinstance(raw_hashes, list):
            false_face_hashes = [str(item) for item in raw_hashes if str(item).strip()]
        return cls(
            last_folder=last_folder,
            blur_strength=clamp_blur_strength(data.get("blur_strength", DEFAULT_BLUR_STRENGTH)),
            language=str(data.get("language") or "ja"),
            face_blur=bool(data.get("face_blur", True)),
            text_blur=bool(data.get("text_blur", False)),
            video_audio=bool(data.get("video_audio", False)),
            enhance_level=parse_enhance_level(
                data["enhance_level"]
                if "enhance_level" in data
                else data.get("auto_enhance", "weak")
            ),
            standby_path=str(data.get("standby_path") or ""),
            use_standby=bool(data.get("use_standby", False)),
            operator_geometry=str(data.get("operator_geometry") or ""),
            output_pos=str(data.get("output_pos") or ""),
            date_from=str(data.get("date_from") or ""),
            date_to=str(data.get("date_to") or ""),
            notes=notes,
            blur_off_confirmed=bool(data.get("blur_off_confirmed", False)),
            recent_folders=recent_folders,
            include_subfolders=bool(data.get("include_subfolders", True)),
            brush_width=clamp_brush_width(data.get("brush_width", DEFAULT_BRUSH_WIDTH)),
            list_sort=parse_list_sort(data.get("list_sort")),
            false_face_hashes=false_face_hashes,
        )


def settings_path() -> Path:
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
