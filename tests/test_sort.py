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


def test_sorted_items_survive_dates_before_1970() -> None:
    # 時計が戻ったカメラの写真（1970 年など）で並べ替えが落ちないこと（Windows の timestamp）
    old = MediaItem(
        path=Path("old.jpg"), kind="image", captured_at=datetime(1969, 12, 31, 9), has_gps=False
    )
    new = MediaItem(
        path=Path("new.jpg"), kind="image", captured_at=datetime(2024, 1, 1), has_gps=False
    )
    assert [it.path.name for it in sorted_items([new, old], "date_desc")] == ["new.jpg", "old.jpg"]
    assert [it.path.name for it in sorted_items([new, old], "date_asc")] == ["old.jpg", "new.jpg"]
