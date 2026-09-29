"""一覧行の短い印。配信中に目で追う用。"""

from __future__ import annotations

from stream_media_viewer.i18n import t

FACE_MARK = "😊"


def row_marks(
    *, favorite: bool, live: bool, ready: bool, manual: bool = False, lang: str = "ja"
) -> str:
    parts: list[str] = []
    if favorite:
        parts.append("⭐")
    if live:
        parts.append(t(lang, "mark_live"))
    if ready:
        parts.append("✓")
    if manual:
        parts.append("💧" + t(lang, "btn_manual"))
    return " ".join(parts)
