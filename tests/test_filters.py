from datetime import datetime

from stream_media_viewer.library.filters import PLACE_NONE, passes_filters


def test_place_none_keeps_items_without_gps() -> None:
    assert passes_filters(has_gps=False, place=PLACE_NONE) is True
    assert passes_filters(has_gps=True, place=PLACE_NONE) is False
    assert passes_filters(has_gps=True, place_name="Kyoto", place="") is True


def test_folder_filter_matches_relative_folder() -> None:
    assert passes_filters(relative_folder="day1", folder="day1") is True
    assert passes_filters(relative_folder="day1", folder="day2") is False
    assert passes_filters(relative_folder="day1", folder="") is True


def test_face_filter_keeps_only_faces() -> None:
    assert passes_filters(has_face=True, faces=True) is True
    assert passes_filters(has_face=False, faces=True) is False
    assert passes_filters(has_face=False, faces=False) is True
    assert passes_filters(place_name="Kyoto", place="Kyoto") is True
    assert passes_filters(place_name="Kyoto", place="Osaka") is False
    assert passes_filters(place_name="Kyoto", place="") is True
    start = datetime(2024, 1, 1).date()
    end = datetime(2024, 12, 31).date()
    assert (
        passes_filters(
            captured_at=None,
            dates=True,
            date_from=start,
            date_to=end,
        )
        is False
    )
    assert (
        passes_filters(
            captured_at=datetime(2024, 6, 1),
            dates=True,
            date_from=start,
            date_to=end,
        )
        is True
    )
