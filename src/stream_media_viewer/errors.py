"""操作画面向けの失敗記録。配信用の窓には出さない。"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

from stream_media_viewer.config import user_config_dir


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


def install_excepthook() -> None:
    def _hook(exc_type: type[BaseException], exc: BaseException, tb) -> None:
        log_exception(exc)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
