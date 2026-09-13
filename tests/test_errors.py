from pathlib import Path

from stream_media_viewer.errors import OPERATOR_ERROR_KEYS, log_exception, user_error_key
from stream_media_viewer.i18n import t


def test_log_exception_writes_error_log(tmp_path) -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        path = log_exception(exc, tmp_path / "error.log")
    text = path.read_text(encoding="utf-8")
    assert "ValueError" in text
    assert "boom" in text


def test_known_failures_have_matching_ja_en_messages() -> None:
    for key in OPERATOR_ERROR_KEYS:
        ja = t("ja", key)
        en = t("en", key)
        assert ja != key
        assert en != key
        assert ja != en


def test_oserror_maps_to_save_failed() -> None:
    assert user_error_key(OSError("disk full"), where="save") == "save_failed"


def test_protect_failure_maps_to_protect_failed() -> None:
    assert user_error_key(RuntimeError("cv2"), where="protect") == "protect_failed"


def test_settings_apply_failure_maps_to_settings_apply_failed() -> None:
    assert user_error_key(ValueError("bad"), where="settings") == "settings_apply_failed"
