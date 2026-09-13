from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileNote:
        marks = data.get("marks") or []
        if not isinstance(marks, list):
            marks = []
        out_ms = data.get("out_ms")
        return cls(
            favorite=bool(data.get("favorite")),
            loop=bool(data.get("loop")),
            in_ms=int(data.get("in_ms") or 0),
            out_ms=None if out_ms is None else int(out_ms),
            marks=[m for m in marks if isinstance(m, dict)],
            has_face=bool(data.get("has_face")),
            has_text_region=bool(data.get("has_text_region")),
            skip_faces=bool(data.get("skip_faces")),
        )
