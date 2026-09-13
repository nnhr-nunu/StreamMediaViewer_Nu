from pathlib import Path

from stream_media_viewer.settings import AppSettings, load_settings, save_settings


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = AppSettings(last_folder="D:/media", blur_strength=40)
    save_settings(original, path)
    loaded = load_settings(path)
    assert loaded.last_folder == "D:/media"
    assert loaded.blur_strength == 40
    assert loaded.face_blur is True
    assert loaded.text_blur is False


def test_missing_settings_file_returns_defaults(tmp_path: Path) -> None:
    loaded = load_settings(tmp_path / "missing.json")
    assert loaded.last_folder == ""
    assert loaded.blur_strength == 25
