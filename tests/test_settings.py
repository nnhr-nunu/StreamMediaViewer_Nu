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
    assert loaded.enhance_level == "weak"
    assert loaded.include_subfolders is True


def test_settings_roundtrip_keeps_detection_flags(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    settings = AppSettings()
    note = settings.note_for("D:/media/a.jpg")
    note.has_face = True
    note.has_text_region = True
    save_settings(settings, path)
    loaded = load_settings(path)
    restored = loaded.note_for("D:/media/a.jpg")
    assert restored.has_face is True
    assert restored.has_text_region is True


def test_blur_strength_is_clamped_to_odd_range(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"blur_strength": 999}', encoding="utf-8")
    assert load_settings(path).blur_strength == 51
    path.write_text('{"blur_strength": 1}', encoding="utf-8")
    assert load_settings(path).blur_strength == 5
    path.write_text('{"blur_strength": 26}', encoding="utf-8")
    assert load_settings(path).blur_strength == 26


def test_old_auto_enhance_true_becomes_weak(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"auto_enhance": false}', encoding="utf-8")
    assert load_settings(path).enhance_level == "off"
    path.write_text('{"auto_enhance": true}', encoding="utf-8")
    assert load_settings(path).enhance_level == "weak"
