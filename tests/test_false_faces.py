from pathlib import Path

from stream_media_viewer.detect.false_faces import (
    effective_false_face_hashes,
    load_shipped_hashes,
    merge_false_face_hashes,
    save_shipped_hashes,
    try_update_shipped_catalog,
)
from stream_media_viewer.settings import AppSettings


def test_merge_false_face_hashes_keeps_order_and_uniques() -> None:
    assert merge_false_face_hashes(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_effective_hashes_include_shipped_and_user(tmp_path: Path, monkeypatch) -> None:
    catalog = tmp_path / "false_face_hashes.json"
    save_shipped_hashes(["shipped1"], catalog)
    monkeypatch.setattr(
        "stream_media_viewer.detect.false_faces.catalog_path", lambda: catalog
    )
    load_shipped_hashes.cache_clear()
    assert "shipped1" in effective_false_face_hashes(["user1"])
    assert "user1" in effective_false_face_hashes(["user1"])
    settings = AppSettings(false_face_hashes=["user1"])
    monkeypatch.setattr(
        "stream_media_viewer.detect.false_faces.catalog_path", lambda: catalog
    )
    load_shipped_hashes.cache_clear()
    assert "shipped1" in settings.all_false_face_hashes()
    assert "user1" in settings.all_false_face_hashes()
    load_shipped_hashes.cache_clear()


def test_try_update_shipped_catalog_writes(tmp_path: Path, monkeypatch) -> None:
    catalog = tmp_path / "false_face_hashes.json"
    monkeypatch.setattr(
        "stream_media_viewer.detect.false_faces.catalog_path", lambda: catalog
    )
    load_shipped_hashes.cache_clear()
    assert try_update_shipped_catalog(["abc"]) is True
    load_shipped_hashes.cache_clear()
    assert "abc" in load_shipped_hashes()
    load_shipped_hashes.cache_clear()
