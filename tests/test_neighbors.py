from stream_media_viewer.library.neighbors import neighbor_rows


def test_neighbor_rows_are_next_and_previous() -> None:
    assert neighbor_rows(0, 1) == ()
    assert neighbor_rows(0, 2) == (1,)
    assert neighbor_rows(1, 2) == (0,)
    assert neighbor_rows(1, 3) == (2, 0)
    assert neighbor_rows(0, 3) == (1, 2)
    assert neighbor_rows(2, 3) == (0, 1)
