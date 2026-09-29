"""一覧の並び。絞り込みとは別に、見える順だけを変える。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stream_media_viewer.library.item import MediaItem

SORT_DATE_ASC = "date_asc"
SORT_DATE_DESC = "date_desc"
SORT_NAME = "name"
SORT_MODES = (SORT_DATE_ASC, SORT_DATE_DESC, SORT_NAME)


_EPOCH = datetime(1970, 1, 1)


def _seconds(value: datetime) -> float:
    # datetime.timestamp() は Windows で 1970 年より前（時計が戻ったカメラなど）だと例外になる
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return (value - _EPOCH).total_seconds()


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
                -_seconds(it.captured_at) if it.captured_at else 0.0,
                it.path.name.lower(),
            ),
        )
    return sorted(
        items,
        key=lambda it: (
            it.captured_at is None,
            _seconds(it.captured_at) if it.captured_at else 0.0,
            it.relative_folder.lower(),
            it.path.name.lower(),
        ),
    )
