"""操作画面向けの失敗記録。配信用の窓には出さない。"""

from __future__ import annotations

import faulthandler
import sys
import traceback
from datetime import datetime
from pathlib import Path

from stream_media_viewer.config import user_config_dir

OPERATOR_ERROR_KEYS = (
    "unreadable",
    "protect_failed",
    "startup_failed",
    "save_failed",
    "settings_load_failed",
    "settings_apply_failed",
    "unexpected_error",
)

_WHERE_TO_KEY = {
    "save": "save_failed",
    "protect": "protect_failed",
    "settings": "settings_apply_failed",
    "load": "settings_load_failed",
    "startup": "startup_failed",
}

_FAULT_LOG = None


def error_log_path() -> Path:
    directory = user_config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "error.log"


def log_exception(exc: BaseException, path: Path | None = None) -> Path:
    target = path or error_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    body = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp}\n{body}\n")
    return target


def user_error_key(_exc: BaseException, *, where: str) -> str:
    return _WHERE_TO_KEY.get(where, "unexpected_error")


def install_excepthook() -> None:
    global _FAULT_LOG
    try:
        _FAULT_LOG = error_log_path().open("a", encoding="utf-8")
        faulthandler.enable(file=_FAULT_LOG, all_threads=True)
    except OSError:
        faulthandler.enable()

    def _hook(exc_type: type[BaseException], exc: BaseException, tb) -> None:
        log_exception(exc)
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            from stream_media_viewer.i18n import t
            from stream_media_viewer.ui.app_icon import apply_app_icon

            qt_app = QApplication.instance()
            if qt_app is not None:
                apply_app_icon(qt_app)
                QMessageBox.critical(
                    None,
                    "StreamMediaViewer(ぬ)",
                    t("ja", "unexpected_error"),
                )
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
