from stream_media_viewer.library.neighbors import neighbor_rows


def test_neighbor_rows_are_next_and_previous() -> None:
    assert neighbor_rows(0, 1) == ()
    assert neighbor_rows(0, 2) == (1,)
    assert neighbor_rows(1, 2) == (0,)
    assert neighbor_rows(1, 3) == (2, 0)
    assert neighbor_rows(0, 3) == (1, 2)
    assert neighbor_rows(2, 3) == (0, 1)


def test_neighbor_rows_prefer_nearer_photos_up_to_five() -> None:
    assert neighbor_rows(0, 12) == (1, 11, 2, 10, 3, 9, 4, 8, 5, 7)
    assert neighbor_rows(5, 12) == (6, 4, 7, 3, 8, 2, 9, 1, 10, 0)
    assert 6 not in neighbor_rows(0, 12)
    assert neighbor_rows(0, 12, radius=1) == (1, 11)
