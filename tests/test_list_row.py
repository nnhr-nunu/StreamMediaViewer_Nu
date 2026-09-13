from stream_media_viewer.ui.list_row import row_marks


def test_row_marks_show_star_live_and_ready_in_that_order() -> None:
    assert row_marks(favorite=True, live=True, ready=True) == "⭐ 【表示中】 ✓"
    assert (
        row_marks(favorite=False, live=False, ready=False, manual=True) == "💧手動ぼかし"
    )


def test_row_marks_omit_what_is_off() -> None:
    assert row_marks(favorite=False, live=True, ready=False) == "【表示中】"
    assert row_marks(favorite=False, live=False, ready=True) == "✓"
    assert row_marks(favorite=False, live=False, ready=False) == ""
