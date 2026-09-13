"""一覧の並び。絞り込みとは別に、見える順だけを変える。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from stream_media_viewer.library.item import MediaItem

SORT_DATE_ASC = "date_asc"
SORT_DATE_DESC = "date_desc"
SORT_NAME = "name"
SORT_MODES = (SORT_DATE_ASC, SORT_DATE_DESC, SORT_NAME)


def parse_list_sort(raw: Any) -> str:
    text = str(raw or "")
    return text if text in SORT_MODES else SORT_DATE_ASC


def sorted_items(items: list[MediaItem], mode: str) -> list[MediaItem]:
    mode = parse_list_sort(mode)
    if mode == SORT_NAME:
        return sorted(items, key=lambda it: (it.path.name.lower(), str(it.path).lower()))
    if mode == SORT_DATE_DESC:
        return sorted(
            items,
            key=lambda it: (
                it.captured_at is None,
                -(it.captured_at.timestamp()) if it.captured_at else 0.0,
                it.path.name.lower(),
            ),
        )
    return sorted(
        items,
        key=lambda it: (
            it.captured_at is None,
            it.captured_at or datetime.min,
            it.relative_folder.lower(),
            it.path.name.lower(),
        ),
    )
