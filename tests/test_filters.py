from datetime import datetime

from stream_media_viewer.library.filters import passes_filters


def test_gps_none_filter_keeps_items_without_location() -> None:
    assert passes_filters(has_gps=False, gps_no=True) is True
    assert passes_filters(has_gps=True, gps_no=True) is False


def test_folder_filter_matches_relative_folder() -> None:
    assert passes_filters(relative_folder="day1", folder="day1") is True
    assert passes_filters(relative_folder="day1", folder="day2") is False
    assert passes_filters(relative_folder="day1", folder="") is True


def test_place_filter_matches_name() -> None:
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
