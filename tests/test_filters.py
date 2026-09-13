from datetime import datetime

from stream_media_viewer.library.filters import passes_filters


def test_gps_none_filter_keeps_items_without_location() -> None:
    assert passes_filters(has_gps=False, gps_no=True) is True
    assert passes_filters(has_gps=True, gps_no=True) is False


def test_place_filter_matches_name() -> None:
    assert passes_filters(place_name="京都 日本", place="京都 日本") is True
    assert passes_filters(place_name="大阪 日本", place="京都 日本") is False
    assert passes_filters(place_name="京都 日本", place="") is True


def test_date_filter_skips_items_without_capture_time() -> None:
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
