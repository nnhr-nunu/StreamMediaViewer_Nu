from stream_media_viewer.settings import remember_folder


def test_remember_folder_puts_latest_first_and_drops_duplicates() -> None:
    first = remember_folder([], "D:/trips/osaka")
    second = remember_folder(first, "D:/trips/tokyo")
    again = remember_folder(second, "D:/trips/osaka")
    assert again[0] == "D:/trips/osaka"
    assert again[1] == "D:/trips/tokyo"
    assert again.count("D:/trips/osaka") == 1


def test_remember_folder_keeps_only_eight() -> None:
    recent: list[str] = []
    for index in range(10):
        recent = remember_folder(recent, f"D:/trips/{index}")
    assert len(recent) == 8
    assert recent[0] == "D:/trips/9"
    assert "D:/trips/0" not in recent
    assert "D:/trips/1" not in recent
