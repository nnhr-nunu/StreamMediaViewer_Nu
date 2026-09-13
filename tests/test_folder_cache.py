from pathlib import Path

from stream_media_viewer.playback.preload import (
    cache_size_bytes,
    clear_folder_cache,
    folder_cache_id,
    item_cache_dir,
)


def test_same_folder_gets_the_same_id(tmp_path: Path) -> None:
    trip = tmp_path / "trip"
    trip.mkdir()
    assert folder_cache_id(trip) == folder_cache_id(trip.resolve())


def test_clearing_one_folder_leaves_the_other(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "stream_media_viewer.playback.preload.preload_root", lambda: tmp_path / "preload"
    )
    id_a = folder_cache_id(tmp_path / "a")
    id_b = folder_cache_id(tmp_path / "b")
    first = item_cache_dir(id_a, "clipA")
    first.mkdir(parents=True)
    (first / "frame.jpg").write_bytes(b"aaa")
    second = item_cache_dir(id_b, "clipB")
    second.mkdir(parents=True)
    (second / "frame.jpg").write_bytes(b"bbbbbbbb")
    assert cache_size_bytes(id_a) == 3
    clear_folder_cache(id_a)
    assert not first.exists()
    assert (second / "frame.jpg").read_bytes() == b"bbbbbbbb"
    assert cache_size_bytes(id_b) == 8
    assert cache_size_bytes() >= 8
