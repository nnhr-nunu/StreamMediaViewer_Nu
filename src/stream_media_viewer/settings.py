"""設定の読み書き。配信出力にはメタデータを載せない。"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stream_media_viewer.config import SETTINGS_FILENAME, user_config_dir
from stream_media_viewer.library.item import FileNote


@dataclass
class AppSettings:
    last_folder: str = ""
    blur_strength: int = 25
    language: str = "ja"
    face_blur: bool = True
    text_blur: bool = False
    video_audio: bool = False
    standby_path: str = ""
    use_standby: bool = False
    operator_geometry: str = ""
    output_pos: str = ""
    date_from: str = ""
    date_to: str = ""
    notes: dict[str, FileNote] = field(default_factory=dict)
    blur_off_confirmed: bool = False

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
            "standby_path": self.standby_path,
            "use_standby": self.use_standby,
            "operator_geometry": self.operator_geometry,
            "output_pos": self.output_pos,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "blur_off_confirmed": self.blur_off_confirmed,
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
        return cls(
            last_folder=str(data.get("last_folder") or ""),
            blur_strength=int(data.get("blur_strength") or 25),
            language=str(data.get("language") or "ja"),
            face_blur=bool(data.get("face_blur", True)),
            text_blur=bool(data.get("text_blur", False)),
            video_audio=bool(data.get("video_audio", False)),
            standby_path=str(data.get("standby_path") or ""),
            use_standby=bool(data.get("use_standby", False)),
            operator_geometry=str(data.get("operator_geometry") or ""),
            output_pos=str(data.get("output_pos") or ""),
            date_from=str(data.get("date_from") or ""),
            date_to=str(data.get("date_to") or ""),
            notes=notes,
            blur_off_confirmed=bool(data.get("blur_off_confirmed", False)),
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
