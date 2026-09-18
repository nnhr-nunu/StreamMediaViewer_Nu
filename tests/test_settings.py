import json
import sys
from pathlib import Path

from stream_media_viewer.settings import (
    FACE_PIPELINE_ACCURATE,
    FACE_PIPELINE_LEGACY,
    AppSettings,
    load_settings,
    load_settings_with_error,
    parse_face_pipeline,
    save_settings,
    settings_path,
)
from stream_media_viewer.ui.overlays import OUTPUT_LOUPE_PX


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
    assert loaded.blur_strength == 180
    assert loaded.enhance_level == "weak"
    assert loaded.include_subfolders is True
    assert loaded.brush_width == 120
    assert loaded.list_sort == "date_asc"
    assert loaded.video_audio is True
    assert loaded.output_loupe_px == OUTPUT_LOUPE_PX


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
    assert restored.skip_faces is False


def test_blur_strength_is_clamped_to_odd_range(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"blur_strength": 999}', encoding="utf-8")
    assert load_settings(path).blur_strength == 300
    path.write_text('{"blur_strength": 1}', encoding="utf-8")
    assert load_settings(path).blur_strength == 5
    path.write_text('{"blur_strength": 26}', encoding="utf-8")
    assert load_settings(path).blur_strength == 26


def test_face_pipeline_defaults_accurate_and_legacy_roundtrips(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    assert parse_face_pipeline(None) == FACE_PIPELINE_ACCURATE
    assert parse_face_pipeline("nope") == FACE_PIPELINE_ACCURATE
    assert parse_face_pipeline("legacy") == FACE_PIPELINE_LEGACY
    assert load_settings(path).face_pipeline == FACE_PIPELINE_ACCURATE
    save_settings(AppSettings(face_pipeline="legacy"), path)
    assert load_settings(path).face_pipeline == FACE_PIPELINE_LEGACY
    path.write_text('{"face_pipeline": "old"}', encoding="utf-8")
    assert load_settings(path).face_pipeline == FACE_PIPELINE_LEGACY


def test_dev_allow_capture_is_hidden_and_omitted_when_off(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    assert load_settings(path).dev_allow_capture is False
    save_settings(AppSettings(), path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "dev_allow_capture" not in raw
    path.write_text('{"dev_allow_capture": true}', encoding="utf-8")
    loaded = load_settings(path)
    assert loaded.dev_allow_capture is True
    save_settings(loaded, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["dev_allow_capture"] is True


def test_video_audio_defaults_on_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{}", encoding="utf-8")
    assert load_settings(path).video_audio is True
    path.write_text('{"video_audio": false}', encoding="utf-8")
    assert load_settings(path).video_audio is False


def test_old_auto_enhance_true_becomes_weak(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"auto_enhance": false}', encoding="utf-8")
    assert load_settings(path).enhance_level == "off"
    path.write_text('{"auto_enhance": true}', encoding="utf-8")
    assert load_settings(path).enhance_level == "weak"


def test_corrupt_settings_file_returns_defaults_and_load_error(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{", encoding="utf-8")
    settings, error_key = load_settings_with_error(path)
    assert settings.blur_strength == 180
    assert error_key == "settings_load_failed"


def test_corrupt_note_is_skipped_not_fatal(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        '{"blur_strength": 40, "notes": {"a.jpg": "broken", "b.jpg": {"favorite": true}}}',
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded.blur_strength == 40
    assert "a.jpg" not in loaded.notes
    assert loaded.note_for("b.jpg").favorite is True


def _freeze_settings(monkeypatch, config: Path, exe_dir: Path) -> None:
    exe_dir.mkdir(parents=True, exist_ok=True)
    exe = exe_dir / "StreamMediaViewer.exe"
    if not exe.exists():
        exe.write_bytes(b"")
    monkeypatch.setattr("stream_media_viewer.settings.user_config_dir", lambda: config)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))


def test_frozen_settings_path_lives_in_user_config_dir(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config"
    _freeze_settings(monkeypatch, config, tmp_path / "app")
    assert settings_path() == config / "settings.json"


def test_frozen_settings_copy_legacy_file_into_user_config(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config"
    exe_dir = tmp_path / "app"
    _freeze_settings(monkeypatch, config, exe_dir)
    (exe_dir / "settings.json").write_text(
        '{"false_face_hashes": ["abc"], "last_folder": "D:/media"}',
        encoding="utf-8",
    )
    target = settings_path()
    loaded = load_settings()
    assert target == config / "settings.json"
    assert target.is_file()
    assert loaded.false_face_hashes == ["abc"]
    assert loaded.last_folder == "D:/media"
    assert (exe_dir / "settings.json").is_file()


def test_frozen_settings_keep_existing_user_config(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "settings.json").write_text(
        '{"false_face_hashes": ["keep"]}',
        encoding="utf-8",
    )
    exe_dir = tmp_path / "app"
    _freeze_settings(monkeypatch, config, exe_dir)
    (exe_dir / "settings.json").write_text(
        '{"false_face_hashes": ["old"]}',
        encoding="utf-8",
    )
    loaded = load_settings()
    assert loaded.false_face_hashes == ["keep"]


def test_source_launch_ignores_settings_beside_python(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config"
    exe_dir = tmp_path / "python"
    exe_dir.mkdir()
    (exe_dir / "settings.json").write_text(
        '{"false_face_hashes": ["nope"]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("stream_media_viewer.settings.user_config_dir", lambda: config)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "python.exe"))
    assert settings_path() == config / "settings.json"
    assert load_settings().false_face_hashes == []
