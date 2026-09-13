"""一覧行の短い印。配信中に目で追う用。"""

from __future__ import annotations


def row_marks(*, favorite: bool, live: bool, ready: bool) -> str:
    parts: list[str] = []
    if favorite:
        parts.append("⭐")
    if live:
        parts.append("【表示中】")
    if ready:
        parts.append("✓")
    return " ".join(parts)
