from pathlib import Path

from stream_media_viewer.ui import app_icon
from stream_media_viewer.ui.app_icon import PROCESS_DISPLAY_NAME, configure_process_identity


def test_process_display_name_is_app_title() -> None:
    assert PROCESS_DISPLAY_NAME == "StreamMediaViewer(ぬ)"


def test_configure_process_identity_sets_console_title(monkeypatch) -> None:
    titles: list[str] = []

    class Kernel:
        @staticmethod
        def SetConsoleTitleW(text: str) -> int:
            titles.append(text)
            return 1

    class Shell:
        @staticmethod
        def SetCurrentProcessExplicitAppUserModelID(_app_id: str) -> int:
            return 0

    class Windll:
        kernel32 = Kernel()
        shell32 = Shell()

    monkeypatch.setattr(app_icon.sys, "platform", "win32")
    monkeypatch.setattr(app_icon.ctypes, "windll", Windll())
    configure_process_identity()
    assert titles == [PROCESS_DISPLAY_NAME]


def test_windows_version_file_names_the_app() -> None:
    text = Path("packaging/windows_version.txt").read_text(encoding="utf-8")
    assert "StreamMediaViewer(ぬ)" in text
    assert "FileDescription" in text
    assert "OriginalFilename" in text
