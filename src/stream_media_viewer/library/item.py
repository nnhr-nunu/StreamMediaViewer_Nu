from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from stream_media_viewer.render.rotate import clamp_rotation


def _as_int(raw: Any, default: int = 0) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default

Kind = Literal["image", "video"]


@dataclass
class MediaItem:
    path: Path
    kind: Kind
    captured_at: datetime | None
    has_gps: bool
    readable: bool = True
    has_face: bool = False
    has_text_region: bool = False
    place_name: str = ""
    relative_folder: str = ""


@dataclass
class FileNote:
    favorite: bool = False
    loop: bool = False
    in_ms: int = 0
    out_ms: int | None = None
    marks: list[dict[str, Any]] = field(default_factory=list)
    has_face: bool = False
    has_text_region: bool = False
    skip_faces: bool = False
    rotation: int = 0
    hidden: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "favorite": self.favorite,
            "loop": self.loop,
            "in_ms": self.in_ms,
            "out_ms": self.out_ms,
            "marks": list(self.marks),
            "has_face": self.has_face,
            "has_text_region": self.has_text_region,
            "skip_faces": self.skip_faces,
            "rotation": clamp_rotation(self.rotation),
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileNote:
        marks = data.get("marks") or []
        if not isinstance(marks, list):
            marks = []
        out_ms = data.get("out_ms")
        parsed_out: int | None
        if out_ms is None:
            parsed_out = None
        else:
            try:
                parsed_out = int(out_ms)
            except (TypeError, ValueError):
                parsed_out = None
        return cls(
            favorite=bool(data.get("favorite")),
            loop=bool(data.get("loop")),
            in_ms=_as_int(data.get("in_ms"), 0),
            out_ms=parsed_out,
            marks=[m for m in marks if isinstance(m, dict)],
            has_face=bool(data.get("has_face")),
            has_text_region=bool(data.get("has_text_region")),
            skip_faces=bool(data.get("skip_faces")),
            rotation=clamp_rotation(data.get("rotation") or 0),
            hidden=bool(data.get("hidden")),
        )
