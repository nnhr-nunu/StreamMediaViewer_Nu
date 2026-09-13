from datetime import datetime
from pathlib import Path

from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.sort import parse_list_sort, sorted_items


def test_parse_list_sort_falls_back_to_oldest() -> None:
    assert parse_list_sort("date_desc") == "date_desc"
    assert parse_list_sort("nope") == "date_asc"


def test_sorted_items_date_and_name() -> None:
    older = MediaItem(
        path=Path("b.jpg"), kind="image", captured_at=datetime(2024, 1, 1), has_gps=False
    )
    newer = MediaItem(
        path=Path("a.jpg"), kind="image", captured_at=datetime(2024, 6, 1), has_gps=False
    )
    undated = MediaItem(path=Path("z.jpg"), kind="image", captured_at=None, has_gps=False)
    items = [newer, undated, older]
    asc = sorted_items(items, "date_asc")
    assert [it.path.name for it in asc] == ["b.jpg", "a.jpg", "z.jpg"]
    desc = sorted_items(items, "date_desc")
    assert [it.path.name for it in desc] == ["a.jpg", "b.jpg", "z.jpg"]
    by_name = sorted_items(items, "name")
    assert [it.path.name for it in by_name] == ["a.jpg", "b.jpg", "z.jpg"]
